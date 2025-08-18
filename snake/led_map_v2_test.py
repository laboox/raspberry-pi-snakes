from snake.led_map_v2 import MAP, NUM_PIXELS


def test_contains_all_chain():
    flat_map = [item for sublist in MAP for item in sublist]
    for i in range(NUM_PIXELS):
        assert i in flat_map, f"Missing {i}"


def test_no_duplicates():
    flat_map = [item for sublist in MAP for item in filter(lambda x: x >= 0, sublist)]
    assert len(set(flat_map)) == NUM_PIXELS, "Duplicates found"
