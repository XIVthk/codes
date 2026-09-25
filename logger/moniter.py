import psutil
from datetime import datetime

class Monitor:
    def __init__(self, logger):
        self.logger = logger
        self.heartbeat_count = 1
    
    def cpu(self):
        return psutil.cpu_percent(interval=1), psutil.cpu_freq().current, psutil.cpu_count()
    
    def memory(self):
        mem = psutil.virtual_memory()
        return mem.percent, mem.used / (1024 ** 3), mem.total / (1024 ** 3)
    
    def disk(self, path="C:/"):
        disk = psutil.disk_usage(path)
        return disk.percent, disk.used / (1024 ** 3), disk.total / (1024 ** 3)

    def heartbeat(self):
        cpu, mhz, cpu_count = self.cpu()
        mem_percent, mem_used, mem_total = self.memory()
        disk_percent, disk_used, disk_total = self.disk()
        disk_free = disk_total - disk_used
        mem_free = mem_total - mem_used

        # D:/
        ddisk_percent, ddisk_used, ddisk_total = self.disk("D:/")
        ddisk_free = ddisk_total - ddisk_used
        
        self.logger.log("\n", "")
        self.logger.log(">", f"Heartbeat #{self.heartbeat_count} ({datetime.now().strftime('%H:%M:%S.%f')[:-3]})")
        self.logger.indent()
        self.logger.log("*", f"CPU: {cpu}% | {mhz:.1f}MHz | {cpu_count} cores")
        self.logger.log("*", f"MEM: {mem_used:.1f}/{mem_total:.1f}GB ({mem_percent}%) | FREE {mem_free:.1f}GB")
        self.logger.log("*", f"DISK C: {disk_used:.1f}/{disk_total:.1f}GB ({disk_percent}%) | FREE {disk_free:.1f}GB")
        self.logger.log("*", f"DISK D: {ddisk_used:.1f}/{ddisk_total:.1f}GB ({ddisk_percent}%) | FREE {ddisk_free:.1f}GB")
        self.logger.dedent()

        warnings = []
        if cpu > 80:
            warnings.append(f"CPU usage is high: {cpu}%")
        if mem_percent > 80:
            warnings.append(f"Memory usage is high: {mem_percent}%")
        if disk_percent > 80:
            warnings.append(f"Disk C usage is high: {disk_percent}%")  
        if ddisk_percent > 80:
            warnings.append(f"Disk D usage is high: {ddisk_percent}%")
        if warnings:
            self.logger.log(">", "Heartbeat warnings:")
            self.logger.indent()
            all(
                self.logger.log("^", warning)
                for warning in warnings
            )
            self.logger.dedent()
        
        self.logger.log("\n", "")
        
        self.heartbeat_count += 1
    
from logger_core import Logger

