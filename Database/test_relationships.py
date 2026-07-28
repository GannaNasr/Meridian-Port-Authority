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


    connection.close()


test_relationships()