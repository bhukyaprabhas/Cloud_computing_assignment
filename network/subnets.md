# Subnet Allocation and Network Access Control (Task 5)

## 1. Subnet Allocation Table

The base network address block allocated is **`10.20.0.0/16`**.

Subnets are allocated in descending order of size (largest host requirement to smallest), contiguous in address space, using the smallest prefix length that satisfies each requirement:

| Subnet | Hosts Needed | Prefix Length | Subnet Mask | Network Address | Usable Host Range | Broadcast Address | Usable Hosts |
|---|---|---|---|---|---|---|---|
| **app** | 1,000 | `/22` | `255.255.252.0` | `10.20.0.0` | `10.20.0.1` – `10.20.3.254` | `10.20.3.255` | 1,022 |
| **public** | 250 | `/24` | `255.255.255.0` | `10.20.4.0` | `10.20.4.1` – `10.20.4.254` | `10.20.4.255` | 254 |
| **data** | 100 | `/25` | `255.255.255.128` | `10.20.5.0` | `10.20.5.1` – `10.20.5.126` | `10.20.5.127` | 126 |
| **management** | 20 | `/27` | `255.255.255.224` | `10.20.5.128` | `10.20.5.129` – `10.20.5.158` | `10.20.5.159` | 30 |

Total addresses allocated: $1024 + 256 + 128 + 32 = 1440$ addresses out of 65,536 available in `10.20.0.0/16`. Unallocated space starts at `10.20.5.160/27`.

---

## 2. Working and Derivation

The rule for usable hosts in an IPv4 subnet with prefix length $p$ is:
$$\text{Usable Hosts} = 2^{32 - p} - 2$$
The two reserved addresses in each subnet are:
1. **Network identifier**: host bits all zeros (first address).
2. **Broadcast address**: host bits all ones (last address).

### 2.1 Subnet `app` (Requirement: 1,000 hosts)
- Minimum host capacity required: $1,000 + 2 = 1,002$ addresses.
- The smallest power of 2 such that $2^h \ge 1,002$ is $2^{10} = 1,024$ ($h = 10$).
- Prefix length: $p = 32 - 10 = 22$ (`/22`).
- Usable hosts: $2^{10} - 2 = 1,022 \ge 1,000$.
- Starting network address: `10.20.0.0`.
- Block size: 1,024 addresses ($4 \times 256$, spanning 3rd octet 0 through 3).
- Network Address: `10.20.0.0`
- Usable Host Range: `10.20.0.1` to `10.20.3.254`
- Broadcast Address: `10.20.3.255`

### 2.2 Subnet `public` (Requirement: 250 hosts)
- Next available address: `10.20.4.0`.
- Minimum host capacity required: $250 + 2 = 252$ addresses.
- The smallest power of 2 such that $2^h \ge 252$ is $2^8 = 256$ ($h = 8$).
- Prefix length: $p = 32 - 8 = 24$ (`/24`).
- Usable hosts: $2^8 - 2 = 254 \ge 250$.
- Starting network address: `10.20.4.0`.
- Block size: 256 addresses (spanning 4th octet 0 through 255).
- Network Address: `10.20.4.0`
- Usable Host Range: `10.20.4.1` to `10.20.4.254`
- Broadcast Address: `10.20.4.255`

### 2.3 Subnet `data` (Requirement: 100 hosts)
- Next available address: `10.20.5.0`.
- Minimum host capacity required: $100 + 2 = 102$ addresses.
- The smallest power of 2 such that $2^h \ge 102$ is $2^7 = 128$ ($h = 7$).
- Prefix length: $p = 32 - 7 = 25$ (`/25`).
- Usable hosts: $2^7 - 2 = 126 \ge 100$.
- Starting network address: `10.20.5.0`.
- Block size: 128 addresses (spanning 4th octet 0 through 127).
- Network Address: `10.20.5.0`
- Usable Host Range: `10.20.5.1` to `10.20.5.126`
- Broadcast Address: `10.20.5.127`

### 2.4 Subnet `management` (Requirement: 20 hosts)
- Next available address: `10.20.5.128`.
- Minimum host capacity required: $20 + 2 = 22$ addresses.
- The smallest power of 2 such that $2^h \ge 22$ is $2^5 = 32$ ($h = 5$).
- Prefix length: $p = 32 - 5 = 27$ (`/27`).
- Usable hosts: $2^5 - 2 = 30 \ge 20$.
- Starting network address: `10.20.5.128`.
- Block size: 32 addresses (spanning 4th octet 128 through 159).
- Network Address: `10.20.5.128`
- Usable Host Range: `10.20.5.129` to `10.20.5.158`
- Broadcast Address: `10.20.5.159`

---

## 3. Stateless NACL Reasoning and Explanations

### 3.1 Why a Stateless NACL Needs Separate Rules for Reply Traffic
A standard stateful firewall tracks active TCP/UDP connections using a state connection table. When an inbound or outbound connection is established and allowed, the firewall automatically permits the corresponding return (reply) packets that belong to that established state (`ESTABLISHED,RELATED`).

In contrast, a **stateless Network Access Control List (NACL)** does not maintain any connection state table or session memory. Every packet is evaluated completely in isolation based strictly on its header fields (direction, protocol, source/destination IP, source/destination port) against the ordered list of rules.

Consequently:
- When an external client initiates a request to the public load balancer on port 80 or 443, the request enters via an **inbound** rule matching destination port 80/443.
- When the load balancer generates the response back to the client, that packet is an **outbound** packet. Since the NACL has no memory of the inbound request, it would silently drop the response unless an explicit outbound rule allows traffic to the client's destination port (which is in the client's ephemeral port range `1024-65535`).
- Similarly, when the load balancer initiates an outbound TCP request to the app subnet on port 8000, the response returned by the backend app server enters the public subnet as an **inbound** packet destined for the load balancer's local ephemeral port (`1024-65535`). An explicit inbound rule matching source CIDR `10.20.0.0/22` and destination ports `1024-65535` is required to permit the backend reply.

Without explicit complementary rules for both directions, bidirectional communication would fail.

### 3.2 Why Rule Order Matters for the 198.51.100.0/24 Block
NACL evaluation follows a strict **first-match** semantics evaluated in increasing numerical order of rule numbers (from lowest rule number to highest). Once a packet matches a rule's criteria (protocol, port range, and CIDR), the designated action (`allow` or `deny`) is immediately applied, and evaluation terminates.

The requirement dictates that **all traffic from `198.51.100.0/24` must be blocked, even on web ports (80 and 443)**.
- The web allow rules permit TCP port 80 and 443 from any IP address (`0.0.0.0/0`).
- Because `198.51.100.0/24` is a subset of `0.0.0.0/0`, any packet from `198.51.100.0/24` destined for port 80 or 443 would match the `0.0.0.0/0` allow rule if that allow rule were evaluated first.
- Therefore, the `deny` rule for `198.51.100.0/24` must be assigned a **strictly lower rule number** (e.g., rule 50) than the general web allow rules (e.g., rules 100 and 110).
- If the deny rule were placed after the allow rule (e.g., rule 200), malicious traffic from `198.51.100.0/24` targeting port 80 or 443 would hit rule 100/110 first, be permitted, and the deny rule would never be evaluated for web traffic.
