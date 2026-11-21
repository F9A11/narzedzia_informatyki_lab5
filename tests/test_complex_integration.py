from src.models import Apartment, ApartmentSettlement, Bill, Parameters, Tenant, TenantSettlement
from src.manager import Manager


def test_load_data():
    parameters = Parameters()
    manager = Manager(parameters)
    assert isinstance(manager.apartments, dict)
    assert isinstance(manager.tenants, dict)
    assert isinstance(manager.transfers, list)
    assert isinstance(manager.bills, list)

    for apartment_key, apartment in manager.apartments.items():
        assert isinstance(apartment, Apartment)
        assert apartment.key == apartment_key


def test_tenants_in_manager():
    parameters = Parameters()
    manager = Manager(parameters)
    assert len(manager.tenants) > 0
    names = [tenant.name for tenant in manager.tenants.values()]
    for tenant in ['Jan Nowak', 'Adam Kowalski', 'Ewa Adamska']:
        assert tenant in names


def test_if_tenants_have_valid_apartment_keys():
    parameters = Parameters()
    manager = Manager(parameters)
    assert manager.check_tenants_apartment_keys() == True

    manager.tenants['tenant-1'].apartment = 'invalid-key'
    assert manager.check_tenants_apartment_keys() == False


def test_get_apartment_costs():
    parameters = Parameters()
    manager = Manager(parameters)

    existing_apartment_key = next(iter(manager.apartments.keys()))

    real_data_cost = manager.get_apartment_costs(existing_apartment_key, 2024, 3)
    assert isinstance(real_data_cost, float)

    manager.bills = [
        Bill(
            amount_pln=200.0,
            date_due='2024-03-10',
            apartment=existing_apartment_key,
            settlement_year=2024,
            settlement_month=3,
            type='prad',
        ),
        Bill(
            amount_pln=250.0,
            date_due='2024-03-20',
            apartment=existing_apartment_key,
            settlement_year=2024,
            settlement_month=3,
            type='woda',
        ),
        Bill(
            amount_pln=300.0,
            date_due='2024-04-10',
            apartment=existing_apartment_key,
            settlement_year=2024,
            settlement_month=4,
            type='prad',
        ),
        Bill(
            amount_pln=150.0,
            date_due='2023-03-10',
            apartment=existing_apartment_key,
            settlement_year=2023,
            settlement_month=3,
            type='prad',
        ),
    ]

    assert manager.get_apartment_costs(existing_apartment_key, 2024, 3) == 450.0
    assert manager.get_apartment_costs(existing_apartment_key, 2024, 5) == 0.0
    assert manager.get_apartment_costs('NON_EXISTENT_APARTMENT', 2024, 3) is None
    assert manager.get_apartment_costs(existing_apartment_key, 2024) == 750.0
    assert manager.get_apartment_costs(existing_apartment_key) == 900.0
    assert manager.get_apartment_costs(existing_apartment_key, 2024, 13) is None
    assert manager.get_apartment_costs(existing_apartment_key, 2024, 0) is None


def test_apartment_costs_with_optional_parameters():
    manager = Manager(Parameters())
    manager.bills.append(Bill(
        apartment='apart-polanka',
        date_due='2025-03-15',
        settlement_year=2025,
        settlement_month=2,
        amount_pln=1250.0,
        type='rent'
    ))

    manager.bills.append(Bill(
        apartment='apart-polanka',
        date_due='2024-03-15',
        settlement_year=2024,
        settlement_month=2,
        amount_pln=1150.0,
        type='rent'
    ))

    manager.bills.append(Bill(
        apartment='apart-polanka',
        date_due='2024-02-02',
        settlement_year=2024,
        settlement_month=1,
        amount_pln=222.0,
        type='electricity'
    ))

    costs = manager.get_apartment_costs('apartment-1', 2024, 1)
    assert costs is None

    costs = manager.get_apartment_costs('apart-polanka', 2024, 3)
    assert costs == 0.0

    costs = manager.get_apartment_costs('apart-polanka', 2024, 1)
    assert costs == 222.0

    costs = manager.get_apartment_costs('apart-polanka', 2025, 1)
    assert costs == 910.0

    costs = manager.get_apartment_costs('apart-polanka', 2024)
    assert costs == 1372.0

    costs = manager.get_apartment_costs('apart-polanka')
    assert costs == 3532.0


def test_create_apartment_settlement():
    parameters = Parameters()
    manager = Manager(parameters)

    existing_apartment_key = next(iter(manager.apartments.keys()))

    manager.bills = [
        Bill(
            amount_pln=200.0,
            date_due='2024-03-10',
            apartment=existing_apartment_key,
            settlement_year=2024,
            settlement_month=3,
            type='prad',
        ),
        Bill(
            amount_pln=150.0,
            date_due='2024-03-20',
            apartment=existing_apartment_key,
            settlement_year=2024,
            settlement_month=3,
            type='woda',
        ),
        # Rachunek z innego miesiąca (nie powinien być wliczony do marca)
        Bill(
            amount_pln=500.0,
            date_due='2024-04-10',
            apartment=existing_apartment_key,
            settlement_year=2024,
            settlement_month=4,
            type='prad',
        ),
    ]

    # 1. Mieszkanie posiada rachunki w danym miesiącu (200.0 + 150.0 = 350.0)
    settlement_with_bills = manager.create_apartment_settlement(existing_apartment_key, 2024, 3)
    assert settlement_with_bills is not None
    assert isinstance(settlement_with_bills, ApartmentSettlement)
    assert settlement_with_bills.apartment == existing_apartment_key
    assert settlement_with_bills.year == 2024
    assert settlement_with_bills.month == 3
    assert settlement_with_bills.total_rent_pln == 0.0
    assert settlement_with_bills.total_bills_pln == 350.0
    assert settlement_with_bills.total_due_pln == 350.0

    # 2. Mieszkanie istnieje, ale nie ma rachunków w danym miesiącu (maj 2024 -> 0.0)
    settlement_no_bills = manager.create_apartment_settlement(existing_apartment_key, 2024, 5)
    assert settlement_no_bills is not None
    assert isinstance(settlement_no_bills, ApartmentSettlement)
    assert settlement_no_bills.apartment == existing_apartment_key
    assert settlement_no_bills.total_rent_pln == 0.0
    assert settlement_no_bills.total_bills_pln == 0.0
    assert settlement_no_bills.total_due_pln == 0.0

    # 3. Przypadki brzegowe: nieistniejące mieszkanie oraz nieprawidłowy miesiąc
    assert manager.create_apartment_settlement('NON_EXISTENT_APARTMENT', 2024, 3) is None
    assert manager.create_apartment_settlement(existing_apartment_key, 2024, 13) is None


def test_create_tenant_settlements():
    parameters = Parameters()
    manager = Manager(parameters)

    # Przygotowujemy kontrolowany zestaw najemców dla trzech scenariuszy:
    # - 'apart-two': 2 najemców
    # - 'apart-one': 1 najemca
    # - 'apart-empty': 0 najemców
    manager.tenants = {
        'tenant-1': Tenant(
            name='Jan Nowak',
            apartment='apart-two',
            room='room-1',
            rent_pln=1500.0,
            deposit_pln=1500.0,
            date_agreement_from='2024-01-01',
            date_agreement_to='2024-12-31',
        ),
        'tenant-2': Tenant(
            name='Anna Kowalska',
            apartment='apart-two',
            room='room-2',
            rent_pln=1600.0,
            deposit_pln=1600.0,
            date_agreement_from='2024-01-01',
            date_agreement_to='2024-12-31',
        ),
        'tenant-3': Tenant(
            name='Piotr Zielinski',
            apartment='apart-one',
            room='room-1',
            rent_pln=2200.0,
            deposit_pln=2200.0,
            date_agreement_from='2024-01-01',
            date_agreement_to='2024-12-31',
        ),
    }

    # 1. Mieszkanie z 2 najemcami (koszt 400.0 -> po 200.0 na osobę)
    apt_settlement_two = ApartmentSettlement(
        apartment='apart-two',
        month=3,
        year=2024,
        total_rent_pln=0.0,
        total_bills_pln=400.0,
        total_due_pln=400.0,
    )
    settlements_two = manager.create_tenant_settlements(apt_settlement_two)
    assert isinstance(settlements_two, list)
    assert len(settlements_two) == 2

    tenant_ids_two = {s.tenant for s in settlements_two}
    assert tenant_ids_two == {'tenant-1', 'tenant-2'}

    for settlement in settlements_two:
        assert isinstance(settlement, TenantSettlement)
        assert settlement.year == 2024
        assert settlement.month == 3
        assert settlement.rent_pln == 0.0
        assert settlement.bills_pln == 200.0
        assert settlement.total_due_pln == 200.0
        assert settlement.balance_pln == -200.0

    # 2. Mieszkanie z 1 najemcą (koszt 350.0 -> całość 350.0 dla jednego najemcy)
    apt_settlement_one = ApartmentSettlement(
        apartment='apart-one',
        month=3,
        year=2024,
        total_rent_pln=0.0,
        total_bills_pln=350.0,
        total_due_pln=350.0,
    )
    settlements_one = manager.create_tenant_settlements(apt_settlement_one)
    assert isinstance(settlements_one, list)
    assert len(settlements_one) == 1
    assert settlements_one[0].tenant == 'tenant-3'
    assert settlements_one[0].bills_pln == 350.0
    assert settlements_one[0].total_due_pln == 350.0
    assert settlements_one[0].balance_pln == -350.0

    # 3. Mieszkanie bez najemców (nie powinny powstać żadne rozliczenia)
    apt_settlement_empty = ApartmentSettlement(
        apartment='apart-empty',
        month=3,
        year=2024,
        total_rent_pln=0.0,
        total_bills_pln=500.0,
        total_due_pln=500.0,
    )
    settlements_empty = manager.create_tenant_settlements(apt_settlement_empty)
    assert isinstance(settlements_empty, list)
    assert len(settlements_empty) == 0