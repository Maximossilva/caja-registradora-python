import json
import uuid
from socio import Socio
from config import PATH_SOCIOS


class RegistroSocio:
    def __init__(self, ruta_archivo=PATH_SOCIOS):
        self._ruta = ruta_archivo
        self._socios = {}
        self._cargar()
        
    def _cargar(self):
        try:
            with open(self._ruta, "r") as archivo:
                data = json.load(archivo)
                
                for datos in data:
                    socio = Socio.from_dict(datos)
                    self._socios[socio.usuario] = socio
                    
        except FileNotFoundError:
            self._socios = {}
    
    def _guardar(self):
        # Lista de dicts para ser consistente con _cargar (que itera sobre la lista)
        data = [socio.to_dict() for socio in self._socios.values()]
        with open(self._ruta, "w") as archivo:
            json.dump(data, archivo, indent=4)
            
    
    def agregar_socio(self,usuario,password):
        if usuario in self._socios:
            raise ValueError("El usuario ya existe")
        
        id_unico = self._generar_id()
        
        nuevo_socio = Socio(
            id_socio = id_unico,
            usuario = usuario,
            password = password
        )
        
        self._socios[usuario] = nuevo_socio
        self._guardar()
        
        return nuevo_socio
    
    def buscar_por_usuario(self,usuario):
        return self._socios.get(usuario)
    
    def autenticar(self,usuario,password):
        socio = self.buscar_por_usuario(usuario)
    
        if socio and socio.validar_password(password):
            return socio
    
        return None
    
    def _generar_id(self):
        return uuid.uuid4().hex