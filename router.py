import json
import curses
import os
from fuzzywuzzy import fuzz

def load_machines(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def ssh_to_machine(ip, port, user):
    print(f"Connecting to {user}@{ip}:{port}...")
    os.system(f"ssh {user}@{ip} -p {port}")

def fuzzy_search(query, machines):
    query = query.lower()
    return sorted(machines, key=lambda x: (-fuzz.partial_ratio(query, x['alias'].lower()), x['alias'].lower()))

def find_match_indices(alias, query):
    alias_lower = alias.lower()
    query_lower = query.lower()
    start = alias_lower.find(query_lower)
    if start == -1:
        return None
    end = start + len(query_lower)
    return (start, end)

def main(stdscr):
    curses.curs_set(1)  # Show cursor
    machines = load_machines('server.json')
    selected_idx = 0
    search_query = ""

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        # Display search bar
        stdscr.addstr(0, 0, f"Search: {search_query}")
        
        # Filter and sort machines based on search query
        filtered_machines = fuzzy_search(search_query, machines)

        # Display machines
        for idx, machine in enumerate(filtered_machines):
            if idx >= height - 2:  # Leave space for search bar and status line
                break
            alias = machine['alias']
            match_indices = find_match_indices(alias, search_query)
            display_text = f"  {alias} ({machine['user']}@{machine['ip']}:{machine['port']})"
            
            if idx == selected_idx:
                stdscr.addstr(idx + 2, 0, "> ", curses.A_REVERSE)
                if match_indices:
                    start, end = match_indices
                    stdscr.addstr(idx + 2, 2, display_text[:start+2], curses.A_REVERSE)
                    stdscr.addstr(idx + 2, start+2, display_text[start+2:end+2], curses.A_REVERSE | curses.A_BOLD | curses.A_UNDERLINE)
                    stdscr.addstr(idx + 2, end+2, display_text[end+2:], curses.A_REVERSE)
                else:
                    stdscr.addstr(idx + 2, 2, display_text, curses.A_REVERSE)
            else:
                if match_indices:
                    start, end = match_indices
                    stdscr.addstr(idx + 2, 0, display_text[:start+2])
                    stdscr.addstr(idx + 2, start+2, display_text[start+2:end+2], curses.A_BOLD | curses.A_UNDERLINE)
                    stdscr.addstr(idx + 2, end+2, display_text[end+2:])
                else:
                    stdscr.addstr(idx + 2, 0, display_text)

        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP and selected_idx > 0:
            selected_idx -= 1
        elif key == curses.KEY_DOWN and selected_idx < min(len(filtered_machines) - 1, height - 3):
            selected_idx += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            if filtered_machines:
                selected_machine = filtered_machines[selected_idx]
                curses.endwin()  # End curses mode
                ssh_to_machine(selected_machine['ip'], selected_machine['port'], selected_machine['user'])
                break
        elif key == 27:  # ESC key
            break
        elif key == curses.KEY_BACKSPACE or key == 127:  # Handle backspace
            search_query = search_query[:-1]
            selected_idx = 0
        elif 32 <= key <= 126:  # Printable ASCII characters
            search_query += chr(key)
            selected_idx = 0

if __name__ == "__main__":
    curses.wrapper(main)