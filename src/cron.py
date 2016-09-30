import datetime
import math
import threading


class CronJob:
    def __init__(self,  interval, channel, message, ignore_silent_mode):
        self.ignore_silent_mode = ignore_silent_mode
        self.interval = interval
        self.channel = channel
        self.message = message

    def get_msg(self):
        return "PRIVMSG #%s :%s" % (self.channel, self.message)


class CronTask(threading.Thread):

    def __init__(self, bot):
        super().__init__()
        # need to store interval last_executed and job
        # maybe during load find shortest interval and set sleep timer to it
        # and each time subtract that from others
        # if no jobs pass run()
        self.__config_manager = bot.get_config_manager()
        self.__connection = bot.get_connection()

        self.__max_sleep_time = None
        self.__cron_jobs = []
        self.__loaded_cron_cfg = None
        self.__running = False

        self.__running_flag = False
        self.stop = threading.Event()
        super().__init__(target=self.__cron_routine, name="cron_thread")

    def load_cron_jobs(self):
        # maybe stop execution for that
        intervals = []
        for job in self.__config_manager["cron"].values():
            self.__cron_jobs.append(CronJob(job["interval"], job["channel"], job["message"], job.get("ignore_silent_mode", False)))
            intervals.append(job["interval"])
        self.__cron_jobs.sort(key=lambda x: x.interval)

        smallest_interval = 0
        for i in intervals:
            if smallest_interval is None:
                smallest_interval = i
            else:
                smallest_interval = math.gcd(smallest_interval, i)

        self.__max_sleep_time = smallest_interval

    def reload_jobs(self):
        # maybe without stopping existing ones
        self.load_cron_jobs()
        self.start()

    def __cron_routine(self):
        # don't start when jobs empty or all disabled
        time_slept = 0
        try:
            while not self.stop.wait(1):
                self.stop.wait(self.__max_sleep_time)
                time_slept += self.__max_sleep_time
                for cj in self.__cron_jobs:
                    if float(time_slept/cj.interval).is_integer():
                        self.__connection.add_raw_msg(cj.get_msg(), cj.ignore_silent_mode)
                        if cj.ignore_silent_mode or not self.__config_manager["general"]["silent_mode"]:
                            print("\033[34;1m{" + datetime.datetime.now().strftime("%H:%M:%S") + "} Cron job executed [%s/%i]\033[0m" % (cj.channel, cj.interval))
                if self.__cron_jobs[-1].interval <= time_slept:
                    time_slept = 0
        finally:
                self.__running_flag = False

    def close(self):
        print("DEBUG: Cron closing")
        self.stop.set()
        self.join()
