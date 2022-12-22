FROM python:3

RUN apt-get -yyy update && apt-get -yyy install software-properties-common && \
    wget -O- https://apt.corretto.aws/corretto.key | apt-key add - && \
    add-apt-repository 'deb https://apt.corretto.aws stable main'

RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    (dpkg -i google-chrome-stable_current_amd64.deb || apt install -y --fix-broken) && \
    rm google-chrome-stable_current_amd64.deb


RUN apt-get -yyy update && apt-get -yyy install java-1.8.0-amazon-corretto-jdk ghostscript


COPY requirements.txt requirements.txt
RUN pip install anvil-app-server
RUN pip install -r requirements.txt
RUN anvil-app-server || true

VOLUME /apps
WORKDIR /apps

COPY LineupApp LineupApp
RUN mkdir /anvil-data

COPY cached-box-scores cached-box-scores
COPY leagues leagues

RUN useradd anvil
RUN useradd python
RUN chown -R anvil:anvil /anvil-data
RUN chmod -R 777 /apps/cached-box-scores
USER anvil


COPY sample_results sample_results
COPY __init__.py __init__.py
COPY simulationConfig.py simulationConfig.py
COPY commitNewRosters.py commitNewRosters.py
COPY game.py game.py
COPY scheduling.py scheduling.py
COPY inning.py inning.py
COPY mlb_api.py mlb_api.py
COPY fatigue.py fatigue.py
COPY processing.py processing.py
COPY simulateLeagueWeek.py simulateLeagueWeek.py
COPY notify_mail.py notify_mail.py
COPY scrapeInjuries.py scrapeInjuries.py
COPY playersTeamsAndPositions.json playersTeamsAndPositions.json


EXPOSE 443

ENTRYPOINT ["anvil-app-server", "--data-dir", "/anvil-data", "--port", "443", "--origin", "https://fantasy.zanzalaz.com"]
CMD ["--app", "LineupApp"]
