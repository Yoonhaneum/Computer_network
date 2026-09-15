task 1 

    resolver : IP를 구하는 것

    1:Root dns 서버는 TLD 서버의 정보를 위임한다
        (www.korea.ac.kr의 경우 .kr로 위임)

    2:TLD 서버에 다시 질문함, 다음 단계의 서버 정보를 반환받음
        (.kr의 경우 ac.kr을 담당하는 서버를 반환)
    
    3: ns와 함께 A - glue 가 있을때(IP 있을때) : 바로 다음 dns 질의를 보냄
       A - glue가 없을때(IP를 주지 않았을때) : 네임 서버의 IP를 별도로 찾아서 2번 과정의 다음으로 넘어감 


    
task 2
    CNAME : 호스트의 별칭 이름
    third-party : 원래 사이트의 도메인과 다른 도메인의 CDN을 이용
    steering : resolver에 따라 다른 IP가 할당됨

    1: --collect 실행 : 12개의 사이트의 CNAME을 계속 따라감. 결과물을 chains.json에 저장함 

    2: thrid-party 식별: 원래 사이트의 registrable domain과 CNAME chain의 최종 도메인의 registrable domain이 다르면 third-party로 판단한다.

    3:resolver 3개(google, quad9, system)가 IP를 확인, resolver별 A 레코드 결과가 모두 같으면 steering이 관찰 X, 그렇지 않으면 steering이 관찰됨. 이번 관찰에서는 12개 중 8개의 steering이 관찰됨

    4. third-party 판별 규칙의 한계
    이 규칙은 도메인 이름만 비교하기 때문에 실제 CDN의 소유 관계까지 정확하게 판단할 수 없다.
    예를 들어 www.wiki"pe"dia.org는 dyna.wiki"me"dia.org로 연결되는데,도메인이 다르기 때문에 이 규칙에서는 third-party로 판단하지만
    실제로는 Wikimedia 계열의 자체 인프라이므로 third-party가 아닐 수 있다.



task 3
    TTL: 캐시된 DNS정보가 유효한 시간
    upstream : 캐시에 없거나 TTL이 만료되었을 때 upstream에 다시 질문
    address, ttl = self.upstream(name)
    stale answer = TTL이 이미 끝났는데도 캐시에 남아 있는 오래된 정보를 반환하면 1, 아니면 0

    1.BaselineCache는 60초동안 데이터를 캐시하므로, 실제 TTL이 10초일때 stale answer를 반환할 수 있다.
    또한 self.entries = [](리스트)를 사용하기 때문에 캐시가 길어질수록 속도가 느려진다

    2. 개선점: 실제 TTL을 사용하여 stale answer 제거, TTL이 지났으면 다시 upstream에 캐시 요청. 리스트 대신 딕셔너리를 사용해서 딕셔너리가 길어져도 이름으로 IP를 찾을수 있음

    3. 
    YourCache는 실제 TTL을 사용하고 dictionary로 캐시를 관리하여 stale answer를 0으로 만들었다. 총 upstream 요청은 275회였다.

    이 workload에서 올바른 캐시가 만들 수 있는 최소 upstream 요청도 275회이다.
    각 이름은 처음 요청할 때 upstream 조회가 필요하고, TTL이 만료된 후 다시 요청될 때도 stale answer를 피하려면 upstream에 다시 조회해야 한다.
    따라서 TTL이 만료된 각 구간의 필수 조회를 모두 합한 275회보다 더 적게 요청하면 TTL이 만료된 캐시 데이터를 사용하게 되어 stale answer가 발생한다.
   