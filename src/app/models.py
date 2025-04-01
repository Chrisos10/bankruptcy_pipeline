from sqlalchemy import Column, Integer, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class BankruptcyData(Base):
    __tablename__ = 'bankruptcy_data'

    id = Column(Integer, primary_key=True, autoincrement=True)
    bankrupt = Column(Integer)
    retained_earnings_to_total_assets = Column(Float)
    total_debt_per_total_net_worth = Column(Float)
    borrowing_dependency = Column(Float)
    persistent_eps_in_the_last_four_seasons = Column(Float)
    continuous_net_profit_growth_rate = Column(Float)
    net_profit_before_tax_per_paidin_capital = Column(Float)
    equity_to_liability = Column(Float)
    pretax_net_interest_rate = Column(Float)
    degree_of_financial_leverage = Column(Float)
    per_share_net_profit_before_tax = Column(Float)
    liability_to_equity = Column(Float)
    net_income_to_total_assets = Column(Float)
    total_income_per_total_expense = Column(Float)
    interest_expense_ratio = Column(Float)
    interest_coverage_ratio = Column(Float)