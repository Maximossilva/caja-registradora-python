productos = {
           "leche": {"precio": 1200.00, "descuento": 0.10, "stock": 100},
            "pan": {"precio": 2000.00, "descuento": 0.05, "stock": 40},
            "huevos": {"precio": 3500.00, "descuento": 0.00, "stock": 60},
            "arroz": {"precio": 1500.00, "descuento": 0.00, "stock": 80},
            "fideos": {"precio": 1100.00, "descuento": 0.00, "stock": 80},
            "aceite": {"precio": 2500.00, "descuento": 0.15, "stock": 30},
            "azucar": {"precio": 900.00, "descuento": 0.00, "stock": 50},
            "cafe": {"precio": 4500.00, "descuento": 0.10, "stock": 25},
            "yerba": {"precio": 3200.00, "descuento": 0.05, "stock": 45},
            "te": {"precio": 800.00, "descuento": 0.00, "stock": 100},
            "manteca": {"precio": 1800.00, "descuento": 0.00, "stock": 35},
            "queso": {"precio": 5500.00, "descuento": 0.05, "stock": 20},
            "jamon": {"precio": 4800.00, "descuento": 0.00, "stock": 15},
            "yogur": {"precio": 1300.00, "descuento": 0.10, "stock": 40},
            "manzana": {"precio": 1400.00, "descuento": 0.00, "stock": 70},
            "banana": {"precio": 1100.00, "descuento": 0.00, "stock": 90},
            "tomate": {"precio": 1600.00, "descuento": 0.00, "stock": 50},
            "papa": {"precio": 800.00, "descuento": 0.00, "stock": 150},
            "cebolla": {"precio": 950.00, "descuento": 0.00, "stock": 100},
            "carne": {"precio": 8500.00, "descuento": 0.05, "stock": 12},
            "pollo": {"precio": 6000.00, "descuento": 0.10, "stock": 20},
            "detergente": {"precio": 2200.00, "descuento": 0.00, "stock": 30},
            "jabon": {"precio": 1200.00, "descuento": 0.00, "stock": 60},
            "shampoo": {"precio": 3800.00, "descuento": 0.15, "stock": 15},
            "papel": {"precio": 2900.00, "descuento": 0.00, "stock": 40},
            "agua": {"precio": 1000.00, "descuento": 0.20, "stock": 120},
            "gaseosa": {"precio": 2400.00, "descuento": 0.00, "stock": 80},
            "galletitas": {"precio": 1700.00, "descuento": 0.05, "stock": 55},
            "harina": {"precio": 1150.00, "descuento": 0.00, "stock": 75},
            "sal": {"precio": 600.00, "descuento": 0.00, "stock": 100}
        }



def ver_stock(stock):
    return stock > 0

def actualizar_stock(stock_actual, cantidad):
    return stock_actual - cantidad