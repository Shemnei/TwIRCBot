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


class CronTask:

    def __init__(self, bot):
        super().__init__()

        self.__config_manager = bot.get_config_manager()
        self.__connection = bot.get_connection()

        self.__max_sleep_time = None
        self.__cron_jobs = None
        self.__loaded_cron_cfg = None
        self.__running = False
        self.__cron_thread = None

        self.__running_flag = False
        self.stop = threading.Event()

    def load_cron_jobs(self):
        self.__cron_jobs = []
        self.__max_sleep_time = None

        intervals = []
        for job in self.__config_manager["cron"].values():
            if job["enabled"]:
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
        print("DEBUG: Cron sleep time set to %is" % self.__max_sleep_time)

    def reload_jobs(self):
        print("DEBUG: Cron jobs reloading")
        self.load_cron_jobs()
        if self.__cron_thread and not self.__cron_thread.is_alive():
            self.start()

    def start(self):
        print("DEBUG: Cron starting")
        self.__cron_thread = threading.Thread(target=self.__cron_routine, name="cron_thread")
        self.__cron_thread.start()

    def __cron_routine(self):
        if not self.__cron_jobs or len(self.__cron_jobs) == 0:
            print("\033[34;1m{" + datetime.datetime.now().strftime("%H:%M:%S") + "} Cron stopped [no jobs]\033[0m")
            return
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
        self.__cron_thread.join()
