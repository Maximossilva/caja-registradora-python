class Caja:
    def __init__(self):
        self.saldo = 0
        
    def ingresar(self,monto):
        self.saldo += monto
    
    def retirar(self,monto):
        if monto > self.saldo:
            raise ValueError("Saldo insuficiente")
        self.saldo -= monto
        return monto
    
    def saldo_actual(self):
        return self.saldo
    

    
    def to_dict(self):
        return {
            "saldo": self.saldo
        }   

