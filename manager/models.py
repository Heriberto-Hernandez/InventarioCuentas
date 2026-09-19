from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
try:
    from .database import Base
except ImportError:
    from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    id_usuario = Column(Integer, primary_key=True, index=True)
    user = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    nombre = Column(String, nullable=False)
    avatar = Column(String, nullable=True)
    google_id = Column(String, unique=True, index=True, nullable=True)

    cuentas = relationship("Cuenta", back_populates="usuario")

class Cuenta(Base):
    __tablename__ = "cuentas"
    id_cuenta = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"))
    user_cuenta = Column(String, unique=True, index=True)
    espacio_maximo = Column(Integer, default=12)

    usuario = relationship("Usuario", back_populates="cuentas")
    inventario = relationship("InventarioCuenta", back_populates="cuenta")

class CatalogoBrainrot(Base):
    __tablename__ = "catalogo_brainrots"
    id_brainrot = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    rareza = Column(String)
    icono = Column(String, default="👾")
    generacion_dinero = Column(Integer, default=100)

class InventarioCuenta(Base):
    __tablename__ = "inventario_cuentas"
    id_inventario = Column(Integer, primary_key=True, index=True)
    id_cuenta = Column(Integer, ForeignKey("cuentas.id_cuenta"))
    id_brainrot = Column(Integer, ForeignKey("catalogo_brainrots.id_brainrot"))
    mutacion = Column(String, default="Normal")

    cuenta = relationship("Cuenta", back_populates="inventario")
    brainrot = relationship("CatalogoBrainrot")