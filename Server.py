
from decimal import Decimal
from wsgiref.simple_server import make_server

from spyne import (
    Application,
    Array,
    ComplexModel,
    Decimal as SoapDecimal,
    Fault,
    Integer,
    ServiceBase,
    Unicode,
    rpc,
)
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication


INVENTARIO = {
    "P001": {"precio": Decimal("25.00"), "stock": 10},
    "P002": {"precio": Decimal("15.00"), "stock": 5},
}

PEDIDOS = {}
SIGUIENTE_ID = 1


class LineaPedido(ComplexModel):
    producto = Unicode(min_occurs=1, min_len=1, nillable=False)
    cantidad = Integer(min_occurs=1, ge=1, nillable=False)


class Pedido(ComplexModel):
    cliente = Unicode(min_occurs=1, min_len=1, nillable=False)
    lineas = Array(
        LineaPedido.customize(min_occurs=1, nillable=False),
        min_occurs=1,
        nillable=False,
    )


class Confirmacion(ComplexModel):
    id = Integer(min_occurs=1, ge=1, nillable=False)
    cliente = Unicode(min_occurs=1, min_len=1, nillable=False)
    total = SoapDecimal(min_occurs=1, ge=0, nillable=False)


class TiendaService(ServiceBase):

    @rpc(Pedido, _returns=Confirmacion)
    def registrar_pedido(ctx, pedido):
        global SIGUIENTE_ID

        if pedido is None or not pedido.cliente or not pedido.lineas:
            raise Fault(
                faultcode="Client.PedidoIncompleto",
                faultstring="El pedido debe incluir un cliente y al menos una linea.",
            )

        cantidades = {}
        total = Decimal("0.00")

        for linea in pedido.lineas:
            codigo = linea.producto
            cantidad = linea.cantidad

            if codigo not in INVENTARIO:
                print(
                    f"[PEDIDO RECHAZADO] Producto inexistente: {codigo}. "
                    "El inventario permanece sin cambios."
                )
                imprimir_inventario()
                raise Fault(
                    faultcode="Client.ProductoInexistente",
                    faultstring=f"El producto {codigo} no existe en el inventario.",
                )

            if cantidad is None or cantidad < 1:
                raise Fault(
                    faultcode="Client.CantidadInvalida",
                    faultstring="La cantidad de cada producto debe ser mayor que cero.",
                )

            cantidades[codigo] = cantidades.get(codigo, 0) + cantidad
            total += INVENTARIO[codigo]["precio"] * cantidad

        for codigo, cantidad_solicitada in cantidades.items():
            stock_actual = INVENTARIO[codigo]["stock"]

            if cantidad_solicitada > stock_actual:
                print(
                    f"[PEDIDO RECHAZADO] Stock insuficiente para {codigo}. "
                    "El inventario completo permanece sin cambios."
                )
                imprimir_inventario()

                raise Fault(
                    faultcode="Client.StockInsuficiente",
                    faultstring=(
                        f"Stock insuficiente para {codigo}. "
                        f"Solicitado: {cantidad_solicitada}; disponible: {stock_actual}."
                    ),
                )

        for codigo, cantidad_solicitada in cantidades.items():
            INVENTARIO[codigo]["stock"] -= cantidad_solicitada

        confirmacion = Confirmacion(
            id=SIGUIENTE_ID,
            cliente=pedido.cliente,
            total=total,
        )

        PEDIDOS[SIGUIENTE_ID] = confirmacion
        SIGUIENTE_ID += 1

        print(
            f"[PEDIDO REGISTRADO] ID: {confirmacion.id} | "
            f"Cliente: {confirmacion.cliente} | Total: ${total:.2f}"
        )

        imprimir_inventario()

        return confirmacion

    @rpc(Integer, _returns=Confirmacion)
    def consultar_pedido(ctx, id):
        pedido = PEDIDOS.get(id)

        if pedido is None:
            raise Fault(
                faultcode="Client.PedidoInexistente",
                faultstring=f"No existe un pedido con el ID {id}.",
            )

        return pedido


def imprimir_inventario():
    print("[INVENTARIO]", end=" ")

    for codigo, datos in INVENTARIO.items():
        print(f"{codigo}: stock={datos['stock']}", end=" | ")

    print()


application = Application(
    [TiendaService],
    tns="tienda.soa",
    in_protocol=Soap11(validator="lxml"),
    out_protocol=Soap11(),
)

wsgi_application = WsgiApplication(application)


if __name__ == "__main__":
    print("Iniciando servicio SOAP de la tienda...")
    imprimir_inventario()

    server = make_server("127.0.0.1", 8000, wsgi_application)

    print("Servidor SOAP iniciado correctamente.")
    print("WSDL: http://127.0.0.1:8000/?wsdl")
    print("Deja esta terminal abierta mientras ejecutas Cliente.py.")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario.")
        server.server_close()
