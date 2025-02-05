FROM ubuntu:20.04

# If you don't update the dockerfile at all, I don't think the github action will update the repos files either.1
# So change this if you want to deploy again
ENV VERSION 2025.1

ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64/

RUN apt-get update -y \
&& apt-get install -y software-properties-common \
&& add-apt-repository ppa:deadsnakes/ppa \
&& apt-get install openjdk-8-jdk -y \
&& apt-get install python3-pip -y \
&& export JAVA_HOME \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

RUN apt-get -yyy update && apt-get -yyy install software-properties-common


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
COPY rosters.py rosters.py
COPY scrapeInjuries.py scrapeInjuries.py
COPY playersTeamsAndPositions.json playersTeamsAndPositions.json


EXPOSE 3030

ENTRYPOINT ["anvil-app-server", "--data-dir", "/anvil-data", "--port", "3030"]
CMD ["--app", "LineupApp"]
