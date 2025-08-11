from snake.led_map import MAP


def test_contains_all_chain():
    flat_map = [item for sublist in MAP for item in sublist]
    for i in range(100):
        assert i in flat_map, f"Missing {i}"


def test_no_duplicates():
    flat_map = [item for sublist in MAP for item in filter(lambda x: x >= 0, sublist)]
    assert len(set(flat_map)) == 100, "Duplicates found"
