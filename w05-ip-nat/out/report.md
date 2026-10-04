W05 IP and NAT Report
    Task 1. Longest Prefix Match
1. IPv4 Address Processing

The _parse_ipv4(address) function validates an IPv4 address and converts it into an integer. It checks whether the address has a valid format and whether each octet is within the range of 0 to 255.

The _int_to_ipv4(value) function performs the reverse operation, converting an integer into the standard dotted-decimal IPv4 format.

These functions allow IPv4 addresses to be processed efficiently as integers.

2. CIDR Parsing and Network Range

The parse_cidr(cidr) function processes a CIDR notation address, which consists of an IPv4 address and a prefix length. It validates the prefix length, generates the corresponding subnet mask, and checks whether the given IP address represents the network address.

The network_range(cidr) function uses the prefix length to determine the range of IP addresses belonging to the network.

3. Routing Table and Longest Prefix Match

The add(self, cidr, next_hop) function adds a network route and its corresponding next hop to the routing table.

The lookup(self, address) function searches the routing table for routes matching a destination IP address. When multiple routes match, it selects the route with the longest prefix length.

This process is called Longest Prefix Match (LPM). It allows a router to select the most specific matching route instead of using a broader network route.

    Task 2. DHCP Packet Analysis
1. DHCP DORA Process

Wireshark was used to capture DHCP packets and examine the address allocation process. The captured packets showed the four stages of DHCP, known as DORA:

Discover: The client broadcasts a request to find available DHCP servers.
Offer: The DHCP server offers an IP address to the client.
Request: The client requests the offered IP address.
ACK: The server confirms the allocation and provides configuration information.
2. Source and Destination Addresses

The DHCP Discover packet used 0.0.0.0 as its source IP address and 255.255.255.255 as its destination IP address.

The client uses 0.0.0.0 because it has not yet obtained an IP address. It uses the broadcast destination 255.255.255.255 because it does not yet know which DHCP server is available on the network.

3. IP Address Allocation and Lease Time

The captured DHCP exchange identified 192.168.0.1 as the DHCP server and 192.168.0.35 as the IP address assigned to the client.

The DHCP ACK packet indicated a lease time of two hours. This means the client can use the assigned IP address for the lease period, subject to the DHCP renewal process and server configuration.

Conclusion

Task 1 covers IPv4 address conversion, CIDR processing, network ranges, and routing table lookup using Longest Prefix Match. Task 2 demonstrates how DHCP automatically assigns IP configuration to a client and how Wireshark can be used to observe the DORA process, broadcast communication, and lease time.


    Task 3. Fast Longest Prefix Match

I implemented YourTable using prefix-length buckets. The table contains 33 dictionaries, one for each IPv4 prefix length from /0 to /32. During lookup, the implementation checks prefixes from the longest to the shortest and returns the next hop as soon as a matching route is found.

This approach improves lookup performance by avoiding a sequential scan of all routing entries. It performs at most 33 dictionary lookups, giving an average lookup complexity of O(33), or O(1) with respect to the number of routes, assuming average constant-time dictionary operations.

The additional memory overhead consists of 33 dictionaries, while the routing entries require O(N) space.

In the benchmark with 5,000 prefixes and 20,000 queries, the implementation achieved 548,210 lookups per second and a measured speedup of 292.3x over the baseline. All lookup results matched the reference implementation.