Task 1
    1. 원본 데이터 original을 2000바이트로 설정함
    
    2. PAYLOAD = 8이므로 original을 8로 나눈다. 250개의 각 데이터 조각에 패킷 번호(시퀀스 번호)를 붙인다
    
    3. Sender가 패킷 하나를 UnreliableChannel에 전달한다
    이때 패킷이 손실, 손상, 순서 바뀜, 지연될 수 있다

    4. Reciver는 채널에서 전달받은 패킷을 하나씩 확인한다.
    4-1. 패킷의 시퀀스 번호가 기다리던 정보라면 PAYLOAD값을 저장하고 ACK(확인응답)을 보낸다

    4-2. 패킷의 시퀀스 번호가 중복되면 payload값을 추가하지 않고 ACK값만 보낸다 

    5. Sender가 올바른 ACK값을 받으면 다음 시퀀스 번호의 패킷을 보낸다.
       ACK를 받지 못하면 현재 ACK를 기다리는 패킷을 다시 전송한다.

    6. 마지막 ACK값을 확인했으면 Sender가 종료된다.

    7. Reciver가 재조립한 데이터를 원본(original)과 비교한다
       SHA-256해시가 동일하면 result   IDENTICAL이 출력된다.

    선택한 프로토콜 : Stop-and-Wait 방식을 선택하였다. 한 번에 하나의 패킷을 전송하고 해당 패킷의 ACK를 확인한 후 다음 패킷을 전송하도록 하였다. 채널에서 패킷의 손실, 중복, 순서 변경이 발생할 수 있기 때문에 ACK를 받지 못한 패킷을 다시 전송할 수 있도록 구성하였다.

    실행 결과 : 
    bytes    sent 2000   received 2000
    channel  {'sent': 674, 'lost': 59, 'duplicated': 22, 'delivered': 637} 
    result   IDENTICAL

    최소 필요 패킷 전송 수 :    2000/ 8 = 250개
    실제로 보낸 패킷 수 :   674개
    최소 필요치의 674/250=2.696배의 패킷을 보냄

    문제점 : 'lost': 59, 'duplicated': 22. lost가 가장 많으며, 어떤 문제가 가장 먼저 발생했는지는 현재의 코드에선 알 수 없다.



Task 2
    # Task 2

## 1. TCP 3-way Handshake

Wireshark에서 `tcp port 443` 필터를 사용하여 TCP 연결을 캡처하였다.

확인한 TCP 3-way handshake는 다음과 같다.

- SYN: Packet 19
- SYN-ACK: Packet 22
- ACK: Packet 23

### Initial Sequence Number

Client의 Initial Sequence Number는 `459827009`이고,
Server의 Initial Sequence Number는 `3902482005`이다.

두 Sequence Number는 0이 아니며 서로 다른 값으로 설정되어 있었다.

TCP Sequence Number는 연결에서 전송되는 바이트의 번호를 나타내며,
연결을 시작할 때 각 측에서 초기값을 선택한다.

## 2. TCP Options

SYN(Packet 19)에서 확인한 TCP 옵션은 다음과 같다.

- MSS: `1460 bytes`
- Window Scale: `8 (×256)`
- SACK Permitted: `Yes`

SYN-ACK(Packet 22)에서 확인한 TCP 옵션은 다음과 같다.

- MSS: `1412 bytes`
- Window Scale: `8 (×256)`
- SACK Permitted: `Yes`

## 3. Advertised Window

SYN(Packet 19)의 Window 값은 `65535`이고
Window Scale은 `256`이었다.

따라서 advertised window는

65535 × 256 = 16,776,960 bytes

이다.

또한 이후 데이터 전송 중 Packet 24에서는
Window 값이 `1024`, Window Scale이 `256`으로 나타났으며,
Wireshark의 Calculated window size는 `262,144 bytes`였다.

Packet 24의 TCP Segment Len은 `759 bytes`였으므로,
이 패킷에서 실제 전송된 TCP payload는 759 bytes였다.

따라서 관찰한 패킷에서는 advertised receive window에 비해
한 패킷에서 전송되는 데이터의 양이 훨씬 작았다.

## 4. Throughput 측정

### Campus Wi-Fi

5회 측정 결과:

- 62.53 Mbps
- 78.81 Mbps
- 76.82 Mbps
- 76.75 Mbps
- 74.99 Mbps

Median throughput: **76.75 Mbps**

Spread: **21%**

Median handshake time: **8.5 ms**

### Tethering

5회 측정 결과:

- 21.81 Mbps
- 29.43 Mbps
- 30.18 Mbps
- 38.58 Mbps
- 29.25 Mbps

Median throughput: **29.43 Mbps**

Spread: **57%**

Median handshake time: **36.3 ms**

## 5. 측정 결과에 대한 관찰

같은 네트워크에서도 5회 측정 결과가 완전히 동일하지 않았다.

Campus Wi-Fi의 throughput spread는 21%였고,
tethering의 spread는 57%였다.

따라서 네트워크 상태와 순간적인 네트워크 부하 등의
영향으로 측정값이 달라질 수 있음을 확인하였다.

또한 campus Wi-Fi의 median handshake time은 8.5 ms,
tethering은 36.3 ms로 차이가 있었다.

Tethering은 campus Wi-Fi보다 median handshake 시간이 더 길었으며,
동시에 측정된 median throughput도 더 낮았다.

TCP 연결에서는 연결이 시작된 후 congestion window가 점진적으로
증가하는 slow start 과정이 있으므로, RTT와 연결 설정에 걸리는 시간이
throughput에 영향을 줄 수 있다. 따라서 handshake time과 throughput은
서로 완전히 독립적인 값으로 볼 수 없다.

Task3
    1.FixedWindow : window값을 항상 64로 설정한다. 항상 64개의 패킷을 동시에 전송한다. ACK와 손실에도 window값 변화 X

    2.YourControl : window값은 1부터 시작함 최대값은 20으로 설정함(실험 환경에서는 링크는 1packet / slot개수 이고 RTT는 20slot이다. 20개의 패킷을 전송하며 링크를 채울수 있다고 계산함)
    ACK를 받을때마다 ack_count가 1 증가하며 현재 window 값 이상이 되면 window를 1 증가시키고 ack_count를 0으로 초기화한다.
    손실(on_loss)가 발생하면 ack_count를 0으로 초기화, window값이 1 감소함

    3.결과
    FixedWindow : 
    - goodput 986.8/1000 slots, 
    - loss 37.4% 
    - average queue가 8.8.

    YourControl : 
    - goodput: 947.5/1000 slots
    - loss: 0.0%
    - retransmission: 0
    - average queue: 0.0

    4. 차이점 : YourControl은 FixedWindow보다 goodput(성공적으로 전달된 데이터)가 낮지만 패킷 손실과 queue가 더 적다. FixedWindow는 높은 goodput을 얻는 대신에 패킷 손실과 queue가 더 많이 발생했다. 
     그러므로 YourControl은 FixedWindow보다 혼잡을 고려하여 전송량을 조절하는 혼잡 제어를 했다고 할 수 있다.