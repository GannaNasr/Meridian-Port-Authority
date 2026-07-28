import sqlite3

DATABASE = "meridian_port.db"

def test_relationships():
    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    print("Testing database relationships...\n")

    # Test 1: Check containers linked with vessels
    cursor.execute("""
        SELECT containers.container_number, vessels.vessel_name
        FROM containers
        JOIN vessels ON containers.vessel_id = vessels.id;
    """)

    containers = cursor.fetchall()

    if containers:
        print("Containers are linked with vessels successfully")
    else:
        print("Container-Vessel relationship failed")


    # Test 2: Check customs holds linked with containers
    cursor.execute("""
        SELECT containers.container_number, customs_holds.hold_reason
        FROM customs_holds
        JOIN containers ON customs_holds.container_id = containers.id;
    """)

    holds = cursor.fetchall()

    if holds:
        print("Customs holds are linked with containers successfully")
    else:
        print("Customs Hold relationship failed")


    # Test 3: Check release orders linked with containers
    cursor.execute("""
        SELECT containers.container_number, release_orders.release_status
        FROM release_orders
        JOIN containers ON release_orders.container_id = containers.id;
    """)

    releases = cursor.fetchall()

    if releases:
        print("Release orders are linked with containers successfully")
    else:
        print("Release Order relationship failed")


    # Test 4: Check customs_holds.officer_id linked with staff
    cursor.execute("""
        SELECT customs_holds.id, staff.name, staff.role
        FROM customs_holds
        JOIN staff ON customs_holds.officer_id = staff.id;
    """)

    hold_officers = cursor.fetchall()

    if hold_officers:
        print("Customs holds are linked with staff (officer_id) successfully")
    else:
        print("Customs Hold - Staff relationship failed")


    # Test 5: Check release_orders.requested_by / approved_by linked with staff
    cursor.execute("""
        SELECT release_orders.id, requester.name, requester.role,
               approver.name, approver.role
        FROM release_orders
        JOIN staff AS requester ON release_orders.requested_by = requester.id
        LEFT JOIN staff AS approver ON release_orders.approved_by = approver.id;
    """)

    release_staff = cursor.fetchall()

    if release_staff:
        print("Release orders are linked with staff (requested_by/approved_by) successfully")
    else:
        print("Release Order - Staff relationship failed")


    # Test 6: Check gate_transactions.processed_by linked with staff
    cursor.execute("""
        SELECT gate_transactions.id, staff.name, staff.role
        FROM gate_transactions
        JOIN staff ON gate_transactions.processed_by = staff.id;
    """)

    gate_staff = cursor.fetchall()

    if gate_staff:
        print("Gate transactions are linked with staff (processed_by) successfully")
    else:
        print("Gate Transaction - Staff relationship failed")


    # Test 7: Check every staff role required by the system actually exists and is active
    cursor.execute("""
        SELECT role, COUNT(*)
        FROM staff
        WHERE active = 1
        GROUP BY role;
    """)

    active_roles = {row[0] for row in cursor.fetchall()}
    required_roles = {"dispatcher", "customs_officer", "supervisor"}

    if required_roles.issubset(active_roles):
        print("All required staff roles (dispatcher, customs_officer, supervisor) are present and active")
    else:
        missing = required_roles - active_roles
        print(f"Missing active staff roles: {missing}")


    connection.close()


test_relationships()