from src.models import (
    Apartment,
    ApartmentSettlement,
    Bill,
    Parameters,
    Tenant,
    TenantSettlement,
    Transfer,
)

class Manager:
    def __init__(self, parameters: Parameters):
        self.parameters = parameters

        self.apartments = {}
        self.tenants = {}
        self.transfers = []
        self.bills = []

        self.load_data()

    def load_data(self):
        self.apartments = Apartment.from_json_file(self.parameters.apartments_json_path)
        self.tenants = Tenant.from_json_file(self.parameters.tenants_json_path)
        self.transfers = Transfer.from_json_file(self.parameters.transfers_json_path)
        self.bills = Bill.from_json_file(self.parameters.bills_json_path)

    def check_tenants_apartment_keys(self) -> bool:
        for tenant in self.tenants.values():
            if tenant.apartment not in self.apartments:
                return False
        return True

    def get_apartment_costs(
        self,
        apartment_key: str,
        year: int | None = None,
        month: int | None = None,
    ) -> float | None:
        if apartment_key not in self.apartments:
            return None

        if month is not None and not (1 <= month <= 12):
            return None

        if month is not None and year is None:
            return None

        total_cost = 0.0
        for bill in self.bills:
            if bill.apartment != apartment_key:
                continue
            if year is not None and bill.settlement_year != year:
                continue
            if month is not None and bill.settlement_month != month:
                continue

            total_cost += bill.amount_pln

        return float(total_cost)

    def create_apartment_settlement(
        self,
        apartment_key: str,
        year: int,
        month: int,
    ) -> ApartmentSettlement | None:
        bills_cost = self.get_apartment_costs(apartment_key, year, month)
        if bills_cost is None:
            return None

        total_rent = 0.0
        return ApartmentSettlement(
            apartment=apartment_key,
            month=month,
            year=year,
            total_rent_pln=total_rent,
            total_bills_pln=bills_cost,
            total_due_pln=total_rent + bills_cost,
        )


    def create_tenant_settlements(
        self,
        apartment_settlement: ApartmentSettlement,
    ) -> list[TenantSettlement]:
        if apartment_settlement is None:
            return []

        apartment_tenants = [
            tenant_key
            for tenant_key, tenant in self.tenants.items()
            if tenant.apartment == apartment_settlement.apartment
        ]

        if not apartment_tenants:
            return []

        bills_per_tenant = apartment_settlement.total_bills_pln / len(apartment_tenants)
        settlement_id = (
            f"{apartment_settlement.apartment}-"
            f"{apartment_settlement.year}-"
            f"{apartment_settlement.month}"
        )

        settlements = []
        for tenant_key in apartment_tenants:
            rent_pln = 0.0
            total_due_pln = rent_pln + bills_per_tenant
            balance_pln = 0.0 - total_due_pln if total_due_pln > 0 else 0.0

            settlements.append(
                TenantSettlement(
                    tenant=tenant_key,
                    apartment_settlement=settlement_id,
                    month=apartment_settlement.month,
                    year=apartment_settlement.year,
                    rent_pln=rent_pln,
                    bills_pln=bills_per_tenant,
                    total_due_pln=total_due_pln,
                    balance_pln=balance_pln,
                )
            )

        return settlements