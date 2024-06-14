from logging import info
from config import Config

from sqlalchemy import Boolean, UniqueConstraint, create_engine, Column, DateTime, ForeignKey, Float, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship


engine = create_engine(
    f"postgresql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_DATABASE}",
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Connector(Base):
    __tablename__ = f"{Config.DB_TABLE_PREFIX}connectors"

    id = Column(Integer, primary_key=True, autoincrement="auto", index=True)
    connector_id = Column(String(36), index=True, nullable=False,)
    power_type =  Column(String(20), nullable=False)
    max_voltage = Column(Integer, nullable=False)
    max_amperage = Column(Integer, nullable=False)

    evse_id = Column(Integer, ForeignKey(f"{Config.DB_TABLE_PREFIX}evses.id"))
    evse = relationship("Evse", back_populates="connectors")

    tariff_id = Column(Integer, ForeignKey(f"{Config.DB_TABLE_PREFIX}tariffs.id"))
    tariff = relationship("Tariff", back_populates="connectors")


class Evse(Base):
    __tablename__ = f"{Config.DB_TABLE_PREFIX}evses"

    id = Column(Integer, primary_key=True, autoincrement="auto", index=True)
    evse_id = Column(String(48), index=True, nullable=False, unique=True)
    ocpp_evse_id = Column(Integer, nullable=False)
    status = Column(String(48), nullable=False)
    station_id = Column(String(255), nullable=False)
    tenant_id = Column(String(3), nullable=False)

    connectors = relationship("Connector", back_populates="evse")

    location_id = Column(Integer, ForeignKey(f"{Config.DB_TABLE_PREFIX}locations.id"))
    location = relationship("Location", back_populates="evses")


class Location(Base):
    __tablename__ = f"{Config.DB_TABLE_PREFIX}locations"

    id = Column(Integer, primary_key=True, autoincrement="auto", index=True)
    location_id = Column(String(36), index=True, nullable=False, unique=True)

    address = Column(String(255),)
    postal_code = Column(String(10))
    city = Column(String(45))
    state = Column(String(45))
    country = Column(String(3))
    
    evses = relationship("Evse", back_populates="location")

    operator_id = Column(Integer, ForeignKey(f"{Config.DB_TABLE_PREFIX}operators.id"))
    operator = relationship("Operator", back_populates="locations")
    

class Operator(Base):
    __tablename__ = f"{Config.DB_TABLE_PREFIX}operators"

    id = Column(Integer, primary_key=True, autoincrement="auto", index=True)
    name = Column(String(255), index=True, nullable=False, unique=True)
    stripe_account_id = Column(String(255), nullable=False, unique=True)
    locations = relationship("Location", back_populates="operator")


class Tariff(Base):
    __tablename__ = f"{Config.DB_TABLE_PREFIX}tariffs"

    id = Column(Integer, primary_key=True, autoincrement="auto", index=True)
    price_kwh = Column(Float, )
    price_minute = Column(Float, )
    price_session = Column(Float,)
    currency = Column(String(3), nullable=False)
    tax_rate = Column(Float, nullable=False)
    authorization_amount = Column(Float, nullable=False)
    payment_fee = Column(Float, nullable=False)
    stripe_price_id = Column(String(255), unique=True)

    connectors = relationship("Connector", back_populates="tariff")


class Checkout(Base):
    __tablename__ = f"{Config.DB_TABLE_PREFIX}checkouts"

    id = Column(Integer, primary_key=True, autoincrement="auto", index=True)
    payment_intent_id = Column(String(255), index=True, unique=True)
    connector_id = Column(Integer, ForeignKey(f"{Config.DB_TABLE_PREFIX}connectors.id"))
    tariff_id = Column(Integer, ForeignKey(f"{Config.DB_TABLE_PREFIX}tariffs.id"))
    qr_code_message_id = Column(Integer, )

    remote_request_status = Column(String(8),)
    remote_request_transaction_id = Column(String(36),)
    
    transaction_start_time = Column(DateTime(timezone=True),)
    transaction_end_time = Column(DateTime(timezone=True),)
    transaction_kwh = Column(Float,)
    power_active_import = Column(Float,)
    transaction_soc = Column(Float,)


# CitrineOS Models
# These are not complete.
# See https://github.com/citrineos/citrineos-core/blob/main/01_Data/src/layers/sequelize/model/
# To review full models


class OcppEvse(Base):
    __tablename__ = "Evses"
    
    databaseId = Column(Integer, primary_key=True, autoincrement="auto", index=True)
    id = Column(Integer, nullable=False )
    connectorId = Column(Integer, )
    
    __table_args__ = (
        
    )

class Transaction(Base):
    __tablename__ = "Transactions"
    
    id = Column(Integer, primary_key=True, autoincrement="auto", index=True)
    stationId = Column(String(255), nullable=False )
    transactionId = Column(String(255), nullable=False )
    isActive = Column(Boolean, nullable=False )
    
    __table_args__ = (
        UniqueConstraint('stationId', 'transactionId', name='stationId_transactionId'),
    )
    
    evseDatabaseId = Column(Integer, ForeignKey("Evses.databaseId"))
    evse = relationship("OcppEvse")
    

class MessageInfo(Base):
    __tablename__ = "MessageInfos"
    
    databaseId = Column(Integer, primary_key=True, autoincrement="auto", index=True)
    stationId = Column(String(255), )
    id = Column(Integer, )
    
    __table_args__ = (
        UniqueConstraint('stationId', 'id', name='stationId_id'),
    )


def init_db() -> None:
    # TODO: add Alembic migrations later
    # info(" [init_db] Deleting database tables.")
    # Base.metadata.drop_all(bind=engine,)
    info(" [init_db] Creating database tables if not exist.")
    Base.metadata.create_all(bind=engine,)
    
    # more things for init here maybe later
    pass


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

