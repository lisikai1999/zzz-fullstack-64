from app.core.music_model import Measure, RepeatMark


def unfold_repeats(measures: list[Measure]) -> list[Measure]:
    """Produce a flat list of measures in performance order."""
    if not measures:
        return []

    n = len(measures)
    result: list[Measure] = []

    segno_pos: int | None = None
    coda_pos: int | None = None
    for i, m in enumerate(measures):
        if RepeatMark.SEGNO in m.repeat_marks:
            segno_pos = i
        if RepeatMark.CODA in m.repeat_marks:
            coda_pos = i

    pos = 0
    repeat_start_stack: list[int] = [0]
    repeat_count: dict[int, int] = {}
    dc_ds_triggered = False
    current_pass = 0  # 0 = first pass, 1 = second pass (after repeat)
    max_iterations = n * 4

    iterations = 0
    while pos < n and iterations < max_iterations:
        iterations += 1
        measure = measures[pos]

        if RepeatMark.REPEAT_START in measure.repeat_marks:
            if not repeat_start_stack or repeat_start_stack[-1] != pos:
                repeat_start_stack.append(pos)

        if measure.volta == 1 and current_pass >= 1:
            pos += 1
            continue
        if measure.volta == 2 and current_pass < 1:
            pos += 1
            continue

        result.append(measure)

        if RepeatMark.FINE in measure.repeat_marks and dc_ds_triggered:
            break

        if RepeatMark.REPEAT_END in measure.repeat_marks:
            count = repeat_count.get(pos, 0)
            if count < 1:
                repeat_count[pos] = count + 1
                current_pass = 1
                jump_to = repeat_start_stack[-1] if repeat_start_stack else 0
                pos = jump_to
                continue
            else:
                current_pass = 0
                if len(repeat_start_stack) > 1:
                    repeat_start_stack.pop()

        if RepeatMark.DC in measure.repeat_marks:
            dc_ds_triggered = True
            pos = 0
            continue

        if RepeatMark.DS in measure.repeat_marks:
            dc_ds_triggered = True
            if segno_pos is not None:
                pos = segno_pos
                continue

        if RepeatMark.CODA in measure.repeat_marks and dc_ds_triggered:
            if coda_pos is not None and coda_pos != pos:
                pos = coda_pos
                continue

        pos += 1

    return result
