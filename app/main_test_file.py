import threading
from app import tasks, queues
from app.mtga_app import check_game_state_forever

if __name__ == "__main__":

    block_watch_process = threading.Thread(target=tasks.block_watch_task, args=(queues.block_read_queue, queues.json_blob_queue, ))
    block_watch_process.start()

    watch = threading.Thread(target=check_game_state_forever)
    watch.start()

    json_watch_process = threading.Thread(target=tasks.json_blob_reader_task, args=(queues.json_blob_queue, queues.json_blob_queue, ))
    json_watch_process.start()
    current_block = ""
    # for line in tailer.follow(open(output_log)):
    with open("../example_logs/single_game.txt", 'r') as rf:
        all_lines = rf.readlines()
        for idx, line in enumerate(all_lines):
            if line.strip() == "":
                queues.block_read_queue.put(current_block)
                current_block = ""
            else:
                current_block += line.strip() + "\n"