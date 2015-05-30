import os
import redis
import logging
import time
import calendar

DATA_DIR_PATH = 'data2/'
TOTAL_FILE_NUM = 11
LOG_ROW_FREQ = 100000
LOG_FILE_NAME = 'load2.log'

# shell script to remove 'https://github.com/' prefix
# sed -i '' 's|https://github.com/||' data2/*.csv

logging.basicConfig(filename=LOG_FILE_NAME,level=logging.DEBUG,format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %I:%M:%S %p')


# generate data file name such as 'user_repo_2-000000000000.csv'
def get_data_file_name(num):
    return 'user_repo_2-'+('%012d' % num)+'.csv'

# load data
def load_starting_from(starting_file_num, starting_row_num):
    current_file_num = -1
    current_row_num = -1
    r = redis.StrictRedis(host='localhost', port=6379, db=0)

    logging.info('Connected to redis...')

    # my csv files have numbers in [0, TOTAL_FILE_NUM)
    for current_file_num in range(starting_file_num, TOTAL_FILE_NUM):
        file_name = get_data_file_name(current_file_num)
        file_path = os.path.join(DATA_DIR_PATH, file_name)
        logging.info('Checking file ' + file_path + '...')

        # file does not exist
        if not os.path.isfile(file_path):
            logging.error('File ' + file_name + 'does not exist')
            continue

        # file exist
        with open(file_path) as f:
            # skip first row containing attribute names
            f.next()
            current_row_num = 1
            # if processing starting_file_num'th file, skip starting_row_num'th rows
            if current_file_num == starting_file_num:
                for i in range(0, starting_row_num):
                    f.next()
                current_row_num += starting_row_num
            # else if processing later file, start from the begining
            else:
                pass

            logging.info('Start processing ' + str(current_file_num) + '\'th file starting at row ' + str(current_row_num))
            # begin actual process of each row
            for line in f:
                row = line.strip('\n').split(',')

                if len(row) < 3:
                    logging.error('Row length less than 3!')
                    current_row_num += 1
                else:
                    user = row[0]
                    repo = row[1]
                    time_string = row[2]
                    time_millisec = calendar.timegm(time.strptime(time_string, '%Y-%m-%d %H:%M:%S'))
                    # previously - r.sadd('login:' + login, repo)
                    r.zadd('user:' + user, time_millisec, repo)
                    r.sadd('repo:' + repo, user)

                current_row_num += 1
                if current_row_num % LOG_ROW_FREQ == 0:
                    logging.info('Done processing ' + str(current_file_num) + '\'th file at row ' + str(current_row_num) + ' including 1st row')

            logging.info('Done processing ' + str(current_file_num) + '\'th file at row ' + str(current_row_num) + ' including 1st row')

if __name__ == '__main__':
    load_starting_from(1, 0)
