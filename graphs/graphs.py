import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib.dates import ConciseDateFormatter

import numpy as np

from datetime import datetime, timedelta

from database.models.contest_model import ContestUserSchema

from bot.main import contest_db
from bot.config import FILES_PATH

from logs.config import logger, extra_params

import asyncio


def _generate_simple_line_plot(numbers_x, numbers_y, int_y: bool = True):
    fig, ax = plt.subplots()
    ax.plot(numbers_x, numbers_y)
    if int_y:
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    return fig, ax


def _generate_contest_users_count_dated_data(
        users: list[ContestUserSchema]) -> tuple:
    if not users:
        return ((datetime.now(), 0),)

    sorted_users_by_date = sorted(users, key=lambda x: x.join_date)
    prev_date = sorted_users_by_date[0].join_date
    dated_data = {prev_date - timedelta(hours=1): 0, prev_date: 1}

    for user in sorted_users_by_date[1::]:
        dated_data[user.join_date] = dated_data[prev_date] + 1
        prev_date = user.join_date

    return tuple(dated_data.items())


def _create_date_graph(date_start: datetime, date_end: datetime,
                       dated_data: tuple | list,
                       time_step_value: int, time_step_format: str,
                       path: str = "line.png",
                       x_label: str = None,
                       y_label: str = None):
    dated_data = sorted(dated_data)
    dates = np.arange(np.datetime64(date_start), np.datetime64(date_end),
                      np.timedelta64(time_step_value, time_step_format))
    y_data = []
    pos = 0
    for date in dates:
        for_data = dated_data[pos::]
        for data in for_data:
            if data[0] <= date:
                y_data.append(data[1])
                pos += 1
                break
        else:
            if not y_data:
                y_data.append(0)
            else:
                y_data.append(y_data[-1])

    y_data[-1] = dated_data[-1][1]

    fig, ax = _generate_simple_line_plot(dates, y_data)

    if x_label:
        ax.set_xlabel(x_label)
    if y_label:
        ax.set_ylabel(y_label)
    ax.xaxis.set_major_formatter(
        ConciseDateFormatter(
            ax.xaxis.get_major_locator()))

    fig.savefig(path, bbox_inches='tight')

    logger.debug(f"generated new dated graph at path: {path}")

    plt.close(fig)


async def generate_contest_users_graph(contest_id: int) -> str:
    contest = await contest_db.get_contest_by_contest_id(contest_id)
    users = await contest_db.get_contest_users(contest_id)

    dated_data = _generate_contest_users_count_dated_data(users)

    if contest.is_finished:
        fin_date = contest.finish_date
    else:
        fin_date = datetime.now()

    start_date = dated_data[0][0]

    if fin_date - start_date <= timedelta(days=3):
        step_format = "h"
    else:
        step_format = "h"
        # нужно еще на больших данных посмотреть есть ли необходимость менять на дни (D)
        # потому что шаг подбирается автоматически

    path = FILES_PATH + f"contest_{contest_id}_graph.png"

    logger.debug(f"generating new dated graph for contest {contest_id}...", extra_params(contest_id=contest_id))
    _create_date_graph(start_date, fin_date, dated_data, 1, step_format,
                       y_label="Количество участников конкурса", path=path)

    return path


# def bar_chart(_numbers, _labels, _pos):
#     plt.bar(_pos, _numbers, color='blue')
#     plt.xticks(ticks=_pos, labels=_labels)
#     plt.show()
#
#
# def pie_chart(_numbers, _labels):
#     fig1, ax1 = plt.subplots()
#     ax1.pie(_numbers, labels=_labels)
#     plt.show()


if __name__ == '__main__':
    # For testing
    asyncio.run(generate_contest_users_graph(24))

    # d_data = _generate_contest_users_count_dated_data([])
    # print(d_data)
    # _create_date_graph(datetime(2024, 7, 10), datetime.now(), d_data, 1, 'D',
    #                    ylabel="Количество участников конкурса")
    # numbers = [2, 1, 4, 6]
    # labels = ['Electric', 'Solar', 'Diesel', 'Unleaded']
    # pos = list(range(4))
    # bar_chart(numbers, labels, pos)
    #
    # numbers = [40, 35, 15, 10]
    # labels = ['Python', 'Ruby', 'C++', 'PHP']
    # pie_chart(numbers, labels)
