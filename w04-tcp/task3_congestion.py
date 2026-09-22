#!/usr/bin/env python3
"""Week 4 · Task 3 — Beat the fixed window.

Textbook §3.7.

`FixedWindow` is a sender that never adapts. It picks a window and keeps it,
forever, no matter what the network says back. It is not a strawman: it is what
you get if you skip congestion control entirely, and it was the internet's
actual failure mode in October 1986.

Write `YourControl` and beat it on the harness:

    python3 bench.py
    python3 bench.py --yours

The interface is two events and one number:

    .window        how many packets you are willing to have in flight
    .on_ack()      one packet made it there and back
    .on_loss()     a packet was dropped, or timed out waiting for its ACK

That is all the information a real TCP sender has. It cannot see the queue,
it cannot see the link rate, and neither can you. You infer them from these
two events, which is the entire idea of §3.7.
"""


class FixedWindow:
    """Send 64 packets at a time and never listen."""

    def __init__(self):
        self.window = 64

    def on_ack(self):
        pass

    def on_loss(self):
        pass


class YourControl:
    """Your congestion control."""

    def __init__(self):
        # 처음에는 작은 window에서 시작
        self.window = 1

        # 링크의 RTT가 20 slots이므로
        # 약 20개의 packet이 pipe를 채울 수 있음
        self.target = 20

        # ACK를 몇 개 받았는지 세기 위한 변수
        self.ack_count = 0

        # 첫 loss가 발생하기 전에는 빠르게 증가
        self.slow_start = True

    def on_ack(self):
        self.ack_count += 1

        if self.window >= self.target:
            # 목표 크기에 도달하면 더 이상 증가시키지 않음
            self.window = self.target
            return

        if self.slow_start:
            # 현재 window만큼 ACK를 받으면 window를 1 증가
            # 결과적으로 천천히 window가 커짐
            if self.ack_count >= self.window:
                self.window += 1
                self.ack_count = 0
        else:
            # loss 이후에는 천천히 증가
            if self.ack_count >= self.window:
                self.window += 1
                self.ack_count = 0

            if self.window > self.target:
                self.window = self.target

    def on_loss(self):
        # loss가 발생하면 혼잡으로 판단
        self.slow_start = False
        self.ack_count = 0

        # 너무 크게 줄이지 않고 1개만 감소
        if self.window > 1:
            self.window -= 1
