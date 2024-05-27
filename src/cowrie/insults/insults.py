
from __future__ import annotations

import hashlib
import os
import time
from typing import Any

from twisted.conch.insults import insults
from twisted.python import log

from cowrie.core import ttylog
from cowrie.core.config import CowrieConfig
from cowrie.shell import protocol


class LoggingServerProtocol(insults.ServerProtocol):
    

    ttylogPath: str = CowrieConfig.get("honeypot", "ttylog_path")
    downloadPath: str = CowrieConfig.get("honeypot", "download_path")
    ttylogEnabled: bool = CowrieConfig.getboolean("honeypot", "ttylog", fallback=True)
    bytesReceivedLimit: int = CowrieConfig.getint(
        "honeypot", "download_limit_size", fallback=0
    )

    def __init__(self, protocolFactory=None, *a, **kw):
        self.type: str
        self.ttylogFile: str
        self.ttylogSize: int = 0
        self.bytesReceived: int = 0
        self.redirFiles: set[list[str]] = set()
        self.redirlogOpen: bool = False  # it will be set at core/protocol.py
        self.stdinlogOpen: bool = False
        self.ttylogOpen: bool = False
        self.terminalProtocol: Any
        self.transport: Any
        self.startTime: float
        self.stdinlogFile: str

        insults.ServerProtocol.__init__(self, protocolFactory, *a, **kw)

        if protocolFactory is protocol.HoneyPotExecProtocol:
            self.type = "e"  # Execcmd
        else:
            self.type = "i"  # Interactive

    def getSessionId(self):
        transportId = self.transport.session.conn.transport.transportId
        channelId = self.transport.session.id
        return (transportId, channelId)

    def connectionMade(self) -> None:
        transportId, channelId = self.getSessionId()
        self.startTime = time.time()

        if self.ttylogEnabled:
            self.ttylogFile = "{}/{}-{}-{}{}.log".format(
                self.ttylogPath,
                time.strftime("%Y%m%d-%H%M%S"),
                transportId,
                channelId,
                self.type,
            )
            ttylog.ttylog_open(self.ttylogFile, self.startTime)
            self.ttylogOpen = True
            self.ttylogSize = 0

        self.stdinlogFile = "{}/{}-{}-{}-stdin.log".format(
            self.downloadPath,
            time.strftime("%Y%m%d-%H%M%S"),
            transportId,
            channelId,
        )

        if self.type == "e":
            self.stdinlogOpen = True
            # log the command into ttylog
            if self.ttylogEnabled:
                (sess, cmd) = self.protocolArgs
                ttylog.ttylog_write(
                    self.ttylogFile, len(cmd), ttylog.TYPE_INTERACT, time.time(), cmd
                )
        else:
            self.stdinlogOpen = False

        insults.ServerProtocol.connectionMade(self)

        if self.type == "e":
            self.terminalProtocol.execcmd.encode("utf8")

    def write(self, data: bytes) -> None:
        if self.ttylogEnabled and self.ttylogOpen:
            ttylog.ttylog_write(
                self.ttylogFile, len(data), ttylog.TYPE_OUTPUT, time.time(), data
            )
            self.ttylogSize += len(data)

        insults.ServerProtocol.write(self, data)

    def dataReceived(self, data: bytes) -> None:
        """
        Input received from user
        """
        self.bytesReceived += len(data)
        if self.bytesReceivedLimit and self.bytesReceived > self.bytesReceivedLimit:
            log.msg(format="Data upload limit reached")
            self.eofReceived()
            return

        if self.stdinlogOpen:
            with open(self.stdinlogFile, "ab") as f:
                f.write(data)
        elif self.ttylogEnabled and self.ttylogOpen:
            ttylog.ttylog_write(
                self.ttylogFile, len(data), ttylog.TYPE_INPUT, time.time(), data
            )

        # prevent crash if something like this was passed:
        # echo cmd ; exit; \n\n
        if self.terminalProtocol:
            insults.ServerProtocol.dataReceived(self, data)

    def eofReceived(self) -> None:
        """
        Receive channel close and pass on to terminal
        """
        if self.terminalProtocol:
            self.terminalProtocol.eofReceived()

    def loseConnection(self) -> None:
        """
        Override super to remove the terminal reset on logout
        """
        self.transport.loseConnection()

    def connectionLost(self, reason):
        """
        FIXME: this method is called 4 times on logout....
        it's called once from Avatar.closed() if disconnected
        """
        if self.stdinlogOpen:
            

                try:
                    log.msg(self.stdinlogFile)
                    self.file_classified(self.stdinlogFile)
                    
                except OSError:
                    pass
                finally:
                    self.stdinlogOpen = False

        if self.redirFiles:
            
                for rp in self.redirFiles:
                    rf = rp[0]

                    if rp[1]:
                        url = rp[1]
                    else:
                        url = rf[rf.find("redir_") + len("redir_") :]

                    try:
                        if not os.path.exists(rf):
                            continue

                        if os.path.getsize(rf) == 0:
                            os.remove(rf)
                            continue

                        with open(rf, "rb") as f:
                            shasum = hashlib.sha256(f.read()).hexdigest()
                            shasumfile = os.path.join(self.downloadPath, shasum)
                            if os.path.exists(shasumfile):
                                os.remove(rf)
                                duplicate = True
                            else:
                                os.rename(rf, shasumfile)
                                duplicate = False
                        log.msg(
                            eventid="cowrie.session.file_download",
                            format="Saved redir contents with SHA-256 %(shasum)s to %(outfile)s",
                            duplicate=duplicate,
                            outfile=shasumfile,
                            shasum=shasum,
                            destfile=url,
                        )
                    except OSError:
                        pass
                self.redirFiles.clear()

        if self.ttylogEnabled and self.ttylogOpen:
            ttylog.ttylog_close(self.ttylogFile, time.time())
            self.ttylogOpen = False
            shasum = ttylog.ttylog_inputhash(self.ttylogFile)
            shasumfile = os.path.join(self.ttylogPath, shasum)

            if os.path.exists(shasumfile):
                duplicate = True
                os.remove(self.ttylogFile)
            else:
                duplicate = False
                os.rename(self.ttylogFile, shasumfile)
                umask = os.umask(0)
                os.umask(umask)
                os.chmod(shasumfile, 0o666 & ~umask)

            log.msg(
                eventid="cowrie.log.closed",
                format="Closing TTY Log: %(ttylog)s after %(duration)d seconds",
                ttylog=shasumfile,
                size=self.ttylogSize,
                shasum=shasum,
                duplicate=duplicate,
                duration=time.time() - self.startTime,
            )

        insults.ServerProtocol.connectionLost(self, reason)

    def file_classified(self, file_name):
        input_file_path=file_name
        folder_path=CowrieConfig.get("honeypot", "classify_path")
        os.chmod(input_file_path, 0o777)
        most_similar_file, similarity = self.find_most_similar_file(input_file_path, folder_path)
        if most_similar_file and similarity>0.03:
           
            destination_file_path = os.path.join(CowrieConfig.get("honeypot", "download_path"), most_similar_file)
            
            os.rename(input_file_path, destination_file_path)
            log.msg(
                        eventid="cowrie.session.file_download",
                        format="Saved stdin contents  %(destination_file_path)s ",
                        destination_file_path=destination_file_path,
                        destfile="",
                    )
            
        else:
            with open(self.stdinlogFile, "rb") as f:
                shasum = hashlib.sha256(f.read()).hexdigest()
                shasumfile = os.path.join(self.downloadPath, shasum)
                if os.path.exists(shasumfile):
                    os.remove(self.stdinlogFile)
                    duplicate = True
                else:
                    os.rename(self.stdinlogFile, shasumfile)
                    duplicate = False
                log.msg(
                            eventid="cowrie.session.file_download",
                            format="Saved stdin contents with SHA-256 %(shasum)s to %(outfile)s",
                            duplicate=duplicate,
                            outfile=shasumfile,
                            shasum=shasum,
                            destfile="",
                        )
            
    def find_most_similar_file(self,input_file, folder_path):

        max_similarity = 0.0
        most_similar_file = None
        for root, dirs,files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                similarity = self.compare_files(input_file, file_path)
                if similarity > max_similarity:
                    max_similarity = similarity
                    most_similar_file = file
        return most_similar_file, max_similarity

    def compare_files(self,file1, file2):
        x=4
        set1 = set()
        set2 = set()
        with open(file1, 'rb') as f1:
            for line in f1:
                line_bytes = line.strip()
                for i in range(0, len(line_bytes), x):
                    set1.add(line_bytes[i:i+x])
        with open(file2, 'rb') as f2:
            for line in f2:
                line_bytes = line.strip()
                for i in range(0, len(line_bytes), x):
                    set2.add(line_bytes[i:i+x])
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        similarity = float(intersection) / float(union)

        return similarity


class LoggingTelnetServerProtocol(LoggingServerProtocol):
    

    def getSessionId(self):
        transportId = self.transport.session.transportId
        sn = self.transport.session.transport.transport.sessionno
        return (transportId, sn)
