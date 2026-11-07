
from zeep import Client
from zeep.exceptions import Fault

WSDL_URL = "http://127.0.0.1:8000/?wsdl"


def mostrar_confirmacion(confirmacion):
    print(f"ID del pedido: {confirmacion.id}")
    print(f"Cliente: {confirmacion.cliente}")
    print(f"Total: ${confirmacion.total:.2f}")


def mostrar_fault(nombre_prueba, accion):
    try:
        accion()
        print(f"{nombre_prueba}: ERROR, se esperaba un Fault y no se recibió.")
    except Fault as error:
        print(f"{nombre_prueba}: Fault {error.code}; {error.message}")
    except Exception as error:
        print(f"{nombre_prueba}: se produjo {type(error).__name__}: {error}")


def probar_datos_incompletos(cliente, descripcion, pedido):
    try:
        cliente.service.registrar_pedido(pedido)
        print(f"{descripcion}: ERROR, el contrato debía rechazar el pedido.")
    except Exception as error:
        print(
            f"{descripcion}: rechazado por el contrato "
            f"({type(error).__name__})."
        )


def main():
    try:
        cliente = Client(WSDL_URL)

        print("Cliente conectado al WSDL:", WSDL_URL)
        print("=" * 72)

        print("PRUEBA 1. PEDIDO VÁLIDO: 2 x P001 + 1 x P002")

        pedido_valido = {
            "cliente": "Alex Demo",
            "lineas": {
                "LineaPedido": [
                    {"producto": "P001", "cantidad": 2},
                    {"producto": "P002", "cantidad": 1},
                ]
            },
        }

        confirmacion = cliente.service.registrar_pedido(pedido_valido)

        mostrar_confirmacion(confirmacion)

        print("Stock esperado después de la compra: P001 = 8; P002 = 4.")
        print("Consulta el inventario actualizado en la terminal del servidor.")
        print("-" * 72)

        print("PRUEBA 2. STOCK INSUFICIENTE: 99 x P002")

        pedido_stock = {
            "cliente": "Alex Demo",
            "lineas": {
                "LineaPedido": [
                    {"producto": "P002", "cantidad": 99}
                ]
            },
        }

        mostrar_fault(
            "Stock insuficiente (el inventario no debe cambiar)",
            lambda: cliente.service.registrar_pedido(pedido_stock),
        )

        print("-" * 72)

        print("PRUEBA 3. PRODUCTO INEXISTENTE: 1 x P999")

        pedido_producto = {
            "cliente": "Alex Demo",
            "lineas": {
                "LineaPedido": [
                    {"producto": "P999", "cantidad": 1}
                ]
            },
        }

        mostrar_fault(
            "Producto inexistente (el inventario no debe cambiar)",
            lambda: cliente.service.registrar_pedido(pedido_producto),
        )

        print("-" * 72)

        print("PRUEBA 4. CONSULTAR PEDIDO EXISTENTE: consultar_pedido(1)")

        consulta = cliente.service.consultar_pedido(1)

        mostrar_confirmacion(consulta)

        print("-" * 72)

        print("PRUEBA 5. CONSULTAR PEDIDO INEXISTENTE: consultar_pedido(50)")

        mostrar_fault(
            "Pedido inexistente",
            lambda: cliente.service.consultar_pedido(50),
        )

        print("-" * 72)

        print("PRUEBA 6. ATOMICIDAD: P001 válido + P002 con stock insuficiente")

        pedido_atomico = {
            "cliente": "Alex Demo",
            "lineas": {
                "LineaPedido": [
                    {"producto": "P001", "cantidad": 1},
                    {"producto": "P002", "cantidad": 99},
                ]
            },
        }

        mostrar_fault(
            "Pedido rechazado completo (P001 tampoco debe descontarse)",
            lambda: cliente.service.registrar_pedido(pedido_atomico),
        )

        print("Comprueba en la terminal del servidor que P001 sigue en 8 y P002 en 4.")

        print("-" * 72)

        print("PRUEBA 7. DATOS INCOMPLETOS: pedido sin líneas")

        probar_datos_incompletos(
            cliente,
            "Pedido sin líneas",
            {"cliente": "Alex Demo"},
        )

        print("PRUEBA 8. DATOS INCOMPLETOS: pedido sin cliente")

        probar_datos_incompletos(
            cliente,
            "Pedido sin cliente",
            {
                "lineas": {
                    "LineaPedido": [
                        {"producto": "P001", "cantidad": 1}
                    ]
                }
            },
        )

        print("=" * 72)
        print("Pruebas del cliente finalizadas.")

    except Exception as error:
        print("No fue posible consumir el servicio SOAP.")
        print("Verifica que Server.py esté ejecutándose y que el WSDL sea correcto.")
        print(f"Detalle: {type(error).__name__}: {error}")


if __name__ == "__main__":
    main()
