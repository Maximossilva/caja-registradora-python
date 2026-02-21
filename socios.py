socios = {
    "francisco" : {"contraseña" : "1234"},
    "pepito" : {"contraseña" : "pepito123"},
    "mario" : {"contraseña" : "jajaxd"}  
}

from config import DESCUENTO_SOCIO

#validacion de socios
def validar_socio(usuario,contraseña):
    if usuario in socios:
        
        #si el usuario y la contraseña coinciden devuelve True
        if socios[usuario]["contraseña"] == contraseña:
            return True #Es socio
    return False #No es socio

def aplicar_descuento_socio(total):
    return total * (1 - DESCUENTO_SOCIO)