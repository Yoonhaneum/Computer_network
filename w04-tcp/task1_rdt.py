
#!/usr/bin/env python3

"""Week 4 · Task 1 — Build reliable delivery on top of an unreliable channel.

Textbook §3.4 (reliable data transfer) and §3.5 (TCP's sequence numbers).

`UnreliableChannel` below loses packets, reorders them, duplicates them, and
delays them. It is the network as §3.4 models it. Your job is to move a file
across it and have the bytes arrive intact and in order.

That is the whole of TCP's reliability story with the congestion control taken
out, and it is worth building once by hand before you ever trust a socket again.

    python3 task1_rdt.py --verify
"""

import argparse
import hashlib
import random

PAYLOAD = 8  # bytes per packet - small, so you see the sequencing


class UnreliableChannel:
    """Loses 10%, duplicates 3%, reorders, and delays. Deterministic by seed.

    You may not make it nicer. You may not read its internals. It is the only
    way your sender can reach your receiver.
    """

    def __init__(self, seed=246, loss=0.10, dup=0.03, reorder=0.10):
        self.rng = random.Random(seed)
        self.loss, self.dup, self.reorder = loss, dup, reorder
        self.wire = []  # packets in flight, in no particular order
        self.stats = {"sent": 0, "lost": 0, "duplicated": 0, "delivered": 0}

    def send(self, packet):
        """Hand a packet to the network. It may never come out."""
        self.stats["sent"] += 1

        if self.rng.random() < self.loss:
            self.stats["lost"] += 1
            return

        copies = 2 if self.rng.random() < self.dup else 1
        self.stats["duplicated"] += copies - 1

        for _ in range(copies):
            if self.rng.random() < self.reorder and self.wire:
                self.wire.insert(
                    self.rng.randrange(len(self.wire)),
                    packet
                )
            else:
                self.wire.append(packet)

    def receive(self):
        """Take the next packet out, or None if the network has nothing."""
        if not self.wire:
            return None

        self.stats["delivered"] += 1
        return self.wire.pop(0)



class Sender:
    """Reliable sender using Stop-and-Wait.

    Packets are sent one at a time.
    The sender waits for the ACK corresponding to the packet currently
    in flight. If the correct ACK does not arrive, the packet is retransmitted.
    """

    def __init__(self, data_channel, ack_channel, data):
        self.data_channel = data_channel
        self.ack_channel = ack_channel

        # Split data into PAYLOAD-sized pieces.
        self.packets = []

        for seq in range(0, len(data), PAYLOAD):
            payload = data[seq:seq + PAYLOAD]
            packet_number = seq // PAYLOAD

            self.packets.append((packet_number, payload))

        # Sequence number of the packet currently being sent.
        self.current = 0

        # True while waiting for the ACK of current packet.
        self.waiting_for_ack = False

        self.finished = False

    def step(self):
        """Do one unit of work.

        Return False when all packets have been acknowledged.
        """

        # All packets have already been acknowledged.
        if self.finished:
            return False

        # Everything has been sent and acknowledged.
        if self.current >= len(self.packets):
            self.finished = True
            return False

        # ---------------------------------------------------------
        # Send / retransmit the current packet
        # ---------------------------------------------------------

        packet = self.packets[self.current]

        # If we are still waiting for its ACK, sending it again
        # is the retransmission.
        #
        # This is necessary because the data packet or its ACK
        # may have been lost.
        self.data_channel.send(packet)
        self.waiting_for_ack = True

        # ---------------------------------------------------------
        # Check for ACK
        # ---------------------------------------------------------

        ack = self.ack_channel.receive()

        if ack is not None:
            # ACK format:
            # ("ACK", sequence_number)

            if (
                isinstance(ack, tuple)
                and len(ack) == 2
                and ack[0] == "ACK"
            ):
                ack_number = ack[1]

                # Only the ACK for the packet we are currently
                # waiting for can move us forward.
                if ack_number == self.current:
                    self.current += 1
                    self.waiting_for_ack = False

                    # All packets acknowledged.
                    if self.current >= len(self.packets):
                        self.finished = True
                        return False

        return True




class Receiver:
    """Reliable receiver.

    Receives packets, removes duplicates, reassembles them in sequence-number
    order, and sends ACKs back to the sender.
    """

    def __init__(self, data_channel, ack_channel):
        self.data_channel = data_channel
        self.ack_channel = ack_channel

        # Next sequence number we are expecting.
        self.expected = 0

        # Store received payloads by sequence number.
        self.received = {}

        # Final reconstructed data.
        self.output = bytearray()

    def step(self):
        packet = self.data_channel.receive()

        # No packet arrived this step.
        if packet is None:
            return

        # Packet format:
        # (sequence_number, payload)
        if (
            not isinstance(packet, tuple)
            or len(packet) != 2
        ):
            return

        seq, payload = packet

        # Ignore invalid sequence numbers.
        if not isinstance(seq, int):
            return

        # ---------------------------------------------------------
        # Correct packet
        # ---------------------------------------------------------
        if seq == self.expected:
            # Store the payload.
            self.received[seq] = payload

            # Reassemble this packet immediately.
            self.output.extend(payload)

            # Tell the sender that this sequence number was received.
            self.ack_channel.send(("ACK", seq))

            # Move to the next expected packet.
            self.expected += 1

        # ---------------------------------------------------------
        # Duplicate packet
        # ---------------------------------------------------------
        elif seq < self.expected:
            # We already received this packet.
            #
            # Do not append its payload again.
            # However, send its ACK again because the sender may not
            # have received the original ACK.
            self.ack_channel.send(("ACK", seq))

        # ---------------------------------------------------------
        # Future/out-of-order packet
        # ---------------------------------------------------------
        else:
            # With Stop-and-Wait this should normally not happen,
            # because the sender only has one outstanding packet.
            #
            # We do not accept it yet.
            # No ACK is necessary here.
            pass

    def data(self):
        """The bytes reassembled so far."""
        return bytes(self.output)


# ------------------------------------------------------------------- harness

def verify(seed=246, size=2000, max_steps=200_000):
    original = bytes(
        random.Random(seed).getrandbits(8)
        for _ in range(size)
    )

    up, down = UnreliableChannel(seed), UnreliableChannel(seed + 1)

    # Data goes out over `up`, ACKs come back over `down`.
    # Both are unreliable.
    sender = Sender(up, down, original)
    receiver = Receiver(up, down)

    for _ in range(max_steps):
        alive = sender.step()
        receiver.step()

        if not alive and len(receiver.data() or b"") >= size:
            break

    got = receiver.data() or b""

    ok = (
        hashlib.sha256(got).hexdigest()
        == hashlib.sha256(original).hexdigest()
    )

    print(f"  bytes    sent {size}   received {len(got)}")
    print(f"  channel  {up.stats}")
    print(f"  result   {'IDENTICAL' if ok else 'CORRUPTED OR INCOMPLETE'}")

    return 0 if ok else 1


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--verify", action="store_true")
    p.add_argument("--seed", type=int, default=246)
    a = p.parse_args()

    raise SystemExit(
        verify(a.seed) if a.verify else p.print_help()
    )

