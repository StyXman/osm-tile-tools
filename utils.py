import bisect
import multiprocessing
import statistics


try:
    NUM_CPUS = multiprocessing.cpu_count()
except NotImplementedError:
    NUM_CPUS = 1


class MedianTracker:
    '''A statistics class '''
    def __init__(self):
        self.items = []


    def add(self, item):
        # TODO: why do they have to be in order?
        index = bisect.bisect(self.items, item)

        self.items.insert(index, item)


    def median(self):
        if len(self.items) == 0:
            return 0

        return statistics.median(self.items)


def floor(i: int, base: int=1) -> int:
    '''Round i down to the closest multiple of base.'''
    return base * (i // base)


def pyramid_count(min_zoom, max_zoom):
    '''Return the amount of tiles of the pyramid between ZLs min and max.'''
    # each pyramid level (ZL) i has 4**i tiles
    return sum([ 4**i for i in range(max_zoom - min_zoom + 1) ])


def time2hms(seconds: float):
    '''Converts time t in seconds into H/M/S.'''
    remaining_seconds = int(seconds)
    hours, remaining_seconds = divmod(remaining_seconds, 3600)
    # minutes, seconds = divmod(remaining_seconds, 60)
    minutes = remaining_seconds // 60
    _, seconds = divmod(seconds, 60)

    return (hours, minutes, seconds)


def log_grafana(text):
    return None
    requests.post('http://localhost:3000/api/annotations',
        auth=('admin', 'Voo}s0zaetaeNgai'),
        json=dict(
            dashboardUID='e907aca7-ea55-4d54-9ade-819b32087f74',
            time=int(datetime.datetime.now().timestamp()*1000),
            text=text,
        )
    )


class SimpleQueue:
    '''Class based on a list that implements the minimum needed to look like a
    *.Queue. The advantage is that there is no (de)serializing here.'''

    def __init__(self, size):
        self.queue = []


    def get(self, block=True, timeout=None):
        if block:
            waited = 0.0

            while len(self.queue) == 0 and (timeout is None or waited < timeout):
                sleep(0.1)
                waited += 0.1

        return self.queue.pop(0)


    def put(self, value, block=True, timeout=None):
        # ignore block and timeout, making it a unbound queue
        # TODO: revisit?
        self.queue.append(value)


    def qsize(self):
        return len(self.queue)


    def remove(self, value):
        try:
            self.queue.remove(value)
        except ValueError:
            # if it's not present, it means it's being rendered
            pass


