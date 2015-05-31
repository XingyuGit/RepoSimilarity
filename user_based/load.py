import os
import redis

if __name__ == '__main__':
    dirpath = 'data/'
    count_row = 0
    count_file = 0
    r = redis.StrictRedis(host='localhost', port=6379, db=0)
    for name in os.listdir(dirpath):
        filepath = os.path.join(dirpath, name)
        if filepath.find('.csv') == -1:
            continue
        if filepath.find('021') == -1:
            continue
        print('processing '+filepath+'...')
        if os.path.isfile(filepath):
            with open(filepath) as f:
                count_file += 1
                next(f)
                print(filepath)
                for line in f:
                    row = line.strip('\n').split(',')
                    # print(row)
                    login = row[0]
                    repo = row[1]
                    count_row += 1
                    r.sadd('login:' + login, repo)
                    r.sadd('repo:' + repo, login)

    print('row processed:' + str(count_row))
    print('file processed:' + str(count_file))
