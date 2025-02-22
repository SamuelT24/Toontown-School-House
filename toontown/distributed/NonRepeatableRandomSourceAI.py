from direct.directnotify.DirectNotifyGlobal import directNotify
from direct.distributed.DistributedObjectAI import DistributedObjectAI
from direct.task import Task
from otp.distributed import OtpDoGlobals
import random


class NonRepeatableRandomSourceAI(DistributedObjectAI):
    notify = directNotify.newCategory('NonRepeatableRandomSourceAI')

    def __init__(self, air):
        DistributedObjectAI.__init__(self, air)

    def announceGenerate(self):
        DistributedObjectAI.announceGenerate(self)
        self._contextGen = SerialMaskedGen((1 << 32)-1)
        self._requests = {}
        # in case the UD goes down before ack-ing, send a sample every few minutes
        self._sampleTask = self.doMethodLater(3 * 60, self._sampleRandomTask, self.uniqueName('sampleRandom'))
        # kick it off right away
        self._sampleRandom()

    def delete(self):
        self.removeTask(self._sampleTask)
        self._sampleTask = None
        DistributedObjectAI.delete(self)

    def _sampleRandomTask(self, task=None):
        self._sampleRandom()
        return Task.again

    def _sampleRandom(self):
        # send over a random sample
        self.air.sendUpdateToDoId('NonRepeatableRandomSource',
                                  'randomSample',
                                  OtpDoGlobals.OTP_DO_ID_TOONTOWN_NON_REPEATABLE_RANDOM_SOURCE,
                                  [self.doId, int(random.randrange(1 << 32))]
                                  )

    def randomSampleAck(self):
        # UD ack'ed the last sample we sent. Send another one. Keeps the UD from getting overloaded
        # with sample messages
        self._sampleRandom()

    def getRandomSamples(self, callback, num=None):
        """
        callback takes list of random samples
        """
        if num is None:
            num = 1
        context = next(self._contextGen)
        self._requests[context] = (callback, )
        self.air.sendUpdateToDoId('NonRepeatableRandomSource',
                                  'getRandomSamples',
                                  OtpDoGlobals.OTP_DO_ID_TOONTOWN_NON_REPEATABLE_RANDOM_SOURCE,
                                  [self.doId, 'NonRepeatableRandomSource', context, num]
                                  )

    def getRandomSamplesReply(self, context, samples):
        callback, = self._requests.pop(context)
        callback(samples)

    if __debug__:
        def printSamples(self, samples):
            print(samples)

        def testRandom(self):
            self.getRandomSamples(self.printSamples, 100)
