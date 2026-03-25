from core import scheduler

if __name__ == "__main__":
    # 创建调度器实例
    control_system = scheduler.Scheduler()

    # 启动调度器
    control_system.start()

    