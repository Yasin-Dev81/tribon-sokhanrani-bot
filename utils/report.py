def generate_progress_bar(percentage, total_width=10):
    filled_width = int(percentage * total_width)
    empty_width = total_width - filled_width

    bar = "█" * filled_width + "▒" * empty_width
    return f"{bar} {percentage*100:0.1f}%"
