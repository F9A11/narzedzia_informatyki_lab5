from src.models import Apartment, Bill, Parameters
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
        # Ten sam rok, inny miesiąc (nie powinno być wliczone)
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