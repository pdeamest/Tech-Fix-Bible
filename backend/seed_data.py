"""
KB Platform · Seed Data
-----------------------
Pure data module with error-code enrichment (migration 004).

Fields per article:
    manufacturer_slug  FK to manufacturers.slug
    title              Natural key (unique per manufacturer)
    description        Full narrative
    source_url         Vendor docs deep link
    tags               Free-form taxonomy
    scenario_type      'troubleshooting' | 'integration' | 'hardening' | 'migration' | 'reference'
    error_codes        [] of vendor-native codes. Format rules:
                         - Uppercase, no whitespace
                         - Prefer vendor-prefixed:  VMW-HA-2017, CTX-4601
                         - Keep raw vendor codes:   EVENT-26, 0x80070005, BGP-4-MSGDUMP
                         - Use HTTP if literal:     HTTP-401, HTTP-429
"""

from __future__ import annotations


MANUFACTURERS: list[dict] = [
    {"slug": "vmware",     "display_name": "VMware by Broadcom",             "website_url": "https://docs.vmware.com"},
    {"slug": "cisco",      "display_name": "Cisco",                          "website_url": "https://www.cisco.com/c/en/us/support"},
    {"slug": "paloalto",   "display_name": "Palo Alto Networks",             "website_url": "https://docs.paloaltonetworks.com"},
    {"slug": "fortinet",   "display_name": "Fortinet",                       "website_url": "https://docs.fortinet.com"},
    {"slug": "checkpoint", "display_name": "Check Point",                    "website_url": "https://sc1.checkpoint.com/documents/latest"},
    {"slug": "juniper",    "display_name": "Juniper Networks",               "website_url": "https://www.juniper.net/documentation"},
    {"slug": "aruba",      "display_name": "Aruba Networks (HPE)",           "website_url": "https://www.arubanetworks.com/techdocs"},
    {"slug": "f5",         "display_name": "F5 Networks",                    "website_url": "https://clouddocs.f5.com"},
    {"slug": "hpe",        "display_name": "Hewlett Packard Enterprise",     "website_url": "https://support.hpe.com"},
    {"slug": "dell",       "display_name": "Dell Technologies",              "website_url": "https://www.dell.com/support"},
    {"slug": "splunk",     "display_name": "Splunk",                         "website_url": "https://docs.splunk.com"},
    {"slug": "citrix",     "display_name": "Citrix (Cloud Software Group)",  "website_url": "https://docs.citrix.com"},
]


ARTICLES: list[dict] = [
    # ── VMware (4) ────────────────────────────────────────────
    {
        "manufacturer_slug": "vmware",
        "title": "vSphere HA Cluster — Heartbeat Datastores & Admission Control",
        "description": "Configure vSphere High Availability with heartbeat datastores, host monitoring levels, VM restart priorities, and admission control policies to guarantee failover capacity in mixed-workload clusters.",
        "source_url": "https://docs.vmware.com/en/VMware-vSphere/8.0/vsphere-availability/GUID-5432CA24-14F1-44E3-87FB-61D937831CF6.html",
        "tags": ["vsphere", "ha", "cluster", "esxi", "vcenter"],
        "scenario_type": "hardening",
        "error_codes": ["VMW-HA-2017", "VMW-HA-1007", "VMW-VC-1000095"],
    },
    {
        "manufacturer_slug": "vmware",
        "title": "vSAN Stretched Cluster with Witness Host Appliance",
        "description": "Deploy vSAN Stretched Cluster across two fault domains with a remote witness appliance. Covers network latency constraints (<5ms RTT), disk group sizing, and automatic failover behavior.",
        "source_url": "https://docs.vmware.com/en/VMware-vSAN/8.0/vsan-planning/GUID-5A01D0C3-8E6B-44A7-9D22-C2D6F6B37E97.html",
        "tags": ["vsan", "stretched-cluster", "witness", "storage"],
        "scenario_type": "integration",
        "error_codes": ["VSAN-60042", "VSAN-60061", "VSAN-WITNESS-1017"],
    },
    {
        "manufacturer_slug": "vmware",
        "title": "NSX-T Micro-segmentation with Distributed Firewall",
        "description": "Implement zero-trust micro-segmentation using NSX-T distributed firewall rules. Tag-based policy creation, workload grouping by OS/app tier, east-west traffic inspection, and Identity Firewall for AD users.",
        "source_url": "https://docs.vmware.com/en/VMware-NSX/4.1/administration/GUID-6AB240DB-949C-4E95-A9A7-4AC6EF5E3036.html",
        "tags": ["nsx-t", "micro-segmentation", "dfw", "zero-trust", "security"],
        "scenario_type": "hardening",
        "error_codes": ["NSX-DFW-1001", "NSX-IDFW-3042"],
    },
    {
        "manufacturer_slug": "vmware",
        "title": "vCenter LDAP / Active Directory SSO Identity Sources",
        "description": "Integrate vCenter Server with Active Directory over LDAP for SSO. Identity source creation, group permissions mapping, and token lifetime configuration.",
        "source_url": "https://docs.vmware.com/en/VMware-vSphere/8.0/vsphere-authentication/GUID-B23B1360-8838-4FF2-B074-71643C4CB040.html",
        "tags": ["vcenter", "ldap", "active-directory", "sso", "authentication"],
        "scenario_type": "integration",
        "error_codes": ["VC-SSO-20003", "VC-SSO-20117", "LDAP-49", "LDAP-81"],
    },

    # ── Cisco (4) ─────────────────────────────────────────────
    {
        "manufacturer_slug": "cisco",
        "title": "OSPF Area Types — Stub, NSSA, Totally Stubby Explained",
        "description": "Detailed comparison of OSPF area types with IOS-XE configuration examples. Explains LSA filtering per type, default route injection, and design recommendations for enterprise topologies.",
        "source_url": "https://www.cisco.com/c/en/us/support/docs/ip/open-shortest-path-first-ospf/13703-8.html",
        "tags": ["ospf", "routing", "ios-xe", "area", "lsa"],
        "scenario_type": "reference",
        "error_codes": ["OSPF-4-ERRRCV", "OSPF-4-CONFLICTING_LSAID", "OSPF-5-ADJCHG"],
    },
    {
        "manufacturer_slug": "cisco",
        "title": "BGP Route Filtering — Prefix Lists, Route Maps & Communities",
        "description": "Granular BGP route filtering using prefix lists combined with route maps. Inbound/outbound filter examples, conditional advertisements, community tagging, and LOCAL_PREF tuning for path selection.",
        "source_url": "https://www.cisco.com/c/en/us/support/docs/ip/border-gateway-protocol-bgp/5441-aggregation.html",
        "tags": ["bgp", "routing", "prefix-list", "route-map", "communities"],
        "scenario_type": "reference",
        "error_codes": ["BGP-3-NOTIFICATION", "BGP-5-ADJCHANGE", "BGP-4-MSGDUMP"],
    },
    {
        "manufacturer_slug": "cisco",
        "title": "802.1Q Trunking, VTP Modes, and Native VLAN Security",
        "description": "Configure IEEE 802.1Q trunking between Catalyst switches. Native VLAN security hardening, pruning allowed VLANs, VTP transparent vs server/client modes, and DTP negotiation disable.",
        "source_url": "https://www.cisco.com/c/en/us/support/docs/lan-switching/8021q/17056-741-4.html",
        "tags": ["vlan", "trunking", "802.1q", "vtp", "switching"],
        "scenario_type": "hardening",
        "error_codes": ["VTP-4-VLANMODERR", "DTP-4-TRUNKPORTCHG", "SPANTREE-2-RECV_1Q_NON_TRUNK"],
    },
    {
        "manufacturer_slug": "cisco",
        "title": "Catalyst 9000 RESTCONF API with Python Automation",
        "description": "Automate Catalyst 9000 using RESTCONF (RFC 8040) with YANG models. Python examples for interface configuration, BGP neighbor queries, streaming telemetry via gRPC, and NETCONF event notifications.",
        "source_url": "https://developer.cisco.com/docs/ios-xe/#!restconf-quick-start-guide",
        "tags": ["restconf", "netconf", "yang", "python", "automation", "catalyst"],
        "scenario_type": "integration",
        "error_codes": ["HTTP-401", "HTTP-409", "YANG-MALFORMED-MSG", "NETCONF-RPC-ERROR"],
    },

    # ── Palo Alto (3) ─────────────────────────────────────────
    {
        "manufacturer_slug": "paloalto",
        "title": "Security Zones Architecture and Policy Rulebase Design",
        "description": "Design a robust security policy using Palo Alto security zones. Zone types (tap, L2, L3, virtual wire), inter-zone policies, Security Profile Groups, and rulebase ordering for optimal performance.",
        "source_url": "https://docs.paloaltonetworks.com/pan-os/11-1/pan-os-admin/policy/security-policy.html",
        "tags": ["palo-alto", "zones", "security-policy", "ngfw", "rulebase"],
        "scenario_type": "hardening",
        "error_codes": ["PAN-COMMIT-10001", "PAN-POLICY-E0004"],
    },
    {
        "manufacturer_slug": "paloalto",
        "title": "GlobalProtect VPN — Certificate Auth & HIP Check Policies",
        "description": "Deploy GlobalProtect with internal/external gateways. Certificate-based authentication, split tunneling, Host Information Profile (HIP) checks for endpoint compliance, and Prisma Access integration.",
        "source_url": "https://docs.paloaltonetworks.com/globalprotect/10-2/globalprotect-admin/host-information.html",
        "tags": ["globalprotect", "vpn", "certificates", "hip", "prisma-access"],
        "scenario_type": "integration",
        "error_codes": ["GP-E-1015", "GP-E-1403", "HIP-PROFILE-MISMATCH"],
    },
    {
        "manufacturer_slug": "paloalto",
        "title": "Panorama Device Groups, Templates, and Config Inheritance",
        "description": "Structure large-scale deployments using Panorama device groups and templates. Inheritance model, template stacks, pre/post rules, Log Forwarding Profiles, and Managed Collector Groups.",
        "source_url": "https://docs.paloaltonetworks.com/panorama/11-1/panorama-admin/manage-firewalls.html",
        "tags": ["panorama", "device-group", "template", "management"],
        "scenario_type": "integration",
        "error_codes": ["PAN-PANORAMA-11003", "PAN-TEMPLATE-CONFLICT-4020"],
    },

    # ── Fortinet (3) ──────────────────────────────────────────
    {
        "manufacturer_slug": "fortinet",
        "title": "FortiGate SD-WAN Performance SLA and Traffic Steering Rules",
        "description": "Configure SD-WAN performance SLA probes (latency, jitter, packet loss) and traffic steering rules. Load balancing algorithms: weighted, spillover, best quality, lowest cost, and custom rule-based steering.",
        "source_url": "https://docs.fortinet.com/document/fortigate/7.4.0/administration-guide/138223/sd-wan",
        "tags": ["fortinet", "sd-wan", "performance-sla", "traffic-steering"],
        "scenario_type": "integration",
        "error_codes": ["FGT-SDWAN-0107", "FGT-HEALTH-CHECK-FAIL"],
    },
    {
        "manufacturer_slug": "fortinet",
        "title": "FortiAnalyzer ADOMs, Log Aggregation, and Report Automation",
        "description": "Configure FortiAnalyzer as centralized log server. ADOMs for multi-tenant logging, log forwarding to SIEM (Splunk, QRadar), scheduled reports with custom SQL datasets, and FortiSOAR alert automation.",
        "source_url": "https://docs.fortinet.com/document/fortianalyzer/7.4.0/administration-guide",
        "tags": ["fortianalyzer", "logging", "siem", "adom", "reports"],
        "scenario_type": "integration",
        "error_codes": ["FAZ-ADOM-0902", "FAZ-LOG-FORWARD-5001"],
    },
    {
        "manufacturer_slug": "fortinet",
        "title": "FortiGate SSL-VPN with RADIUS and FortiToken MFA",
        "description": "Deploy SSL-VPN with two-factor authentication via RADIUS + FortiToken Mobile. Web-mode vs tunnel-mode clients, split tunneling configuration, SSL certificate management, and auth failure troubleshooting.",
        "source_url": "https://docs.fortinet.com/document/fortigate/7.4.0/administration-guide/954635/ssl-vpn",
        "tags": ["fortigate", "ssl-vpn", "radius", "mfa", "fortitoken"],
        "scenario_type": "integration",
        "error_codes": ["FGT-SSLVPN-7026", "FGT-AUTH-FAIL-0103", "RADIUS-REJECT-28"],
    },

    # ── Check Point (2) ───────────────────────────────────────
    {
        "manufacturer_slug": "checkpoint",
        "title": "SmartConsole Policy Layers, Inline Layers, and Installation",
        "description": "Manage security policies in Check Point SmartConsole R81.20. Policy layer architecture, inline layers for granular control, desktop security policies, and optimizing installation time on large gateways.",
        "source_url": "https://sc1.checkpoint.com/documents/R81.20/WebAdminGuides/EN/CP_R81.20_SecurityManagement_AdminGuide/Default.htm",
        "tags": ["checkpoint", "smartconsole", "policy", "layers", "r81"],
        "scenario_type": "hardening",
        "error_codes": ["CP-POLICY-INSTALL-0201", "CP-FWD-VERIFIER-1402"],
    },
    {
        "manufacturer_slug": "checkpoint",
        "title": "ClusterXL Active-Active Load Sharing and Maestro HyperScale",
        "description": "Deploy ClusterXL in Active-Active Load Sharing mode with CCP (Cluster Control Protocol), sticky connections, delta sync. Extends to Maestro Hyperscale for 1M+ connections/sec throughput.",
        "source_url": "https://sc1.checkpoint.com/documents/R81.20/WebAdminGuides/EN/CP_R81.20_ClusterXL_AdminGuide/Default.htm",
        "tags": ["checkpoint", "clusterxl", "ha", "load-sharing", "maestro"],
        "scenario_type": "integration",
        "error_codes": ["CP-CLUSTER-101", "CP-CCP-2307", "CP-MAESTRO-6001"],
    },

    # ── Juniper (2) ───────────────────────────────────────────
    {
        "manufacturer_slug": "juniper",
        "title": "JunOS MPLS LDP and RSVP-TE Traffic Engineering on MX Series",
        "description": "Configure MPLS with LDP and RSVP-TE on MX Series. LSP path creation, CSPF-based computation, Fast Reroute (FRR) with link/node protection, and MPLS OAM tools (ping, traceroute).",
        "source_url": "https://www.juniper.net/documentation/us/en/software/junos/mpls/topics/topic-map/mpls-overview.html",
        "tags": ["junos", "mpls", "ldp", "rsvp", "traffic-engineering"],
        "scenario_type": "reference",
        "error_codes": ["RPD-LDP-SESSION_DOWN", "RPD-RSVP-PATHERR", "RPD-MPLS-LSP-DOWN"],
    },
    {
        "manufacturer_slug": "juniper",
        "title": "SRX Application-Level Gateways — SIP, H.323, FTP ALG",
        "description": "Enable and configure Application-Level Gateways on SRX for NAT traversal. SIP/H.323 for VoIP, FTP active mode passthrough, RTSP media streams, and troubleshooting common ALG issues.",
        "source_url": "https://www.juniper.net/documentation/us/en/software/junos/alg/topics/topic-map/security-alg-overview.html",
        "tags": ["juniper", "srx", "alg", "nat", "voip", "sip"],
        "scenario_type": "troubleshooting",
        "error_codes": ["FLOW-ALG-SIP-INVALID", "FLOW-ALG-FTP-DROP"],
    },

    # ── F5 (2) ────────────────────────────────────────────────
    {
        "manufacturer_slug": "f5",
        "title": "BIG-IP iRules — SSL Offload, X-Forwarded-For, Persistence",
        "description": "Write iRules for SSL termination, HTTP header manipulation (XFF insertion, cookie-based persistence), URI rewriting, client certificate extraction, and rate-limiting on F5 BIG-IP LTM.",
        "source_url": "https://clouddocs.f5.com/api/irules/",
        "tags": ["f5", "big-ip", "irules", "ssl", "http", "ltm", "persistence"],
        "scenario_type": "reference",
        "error_codes": ["TCL-ERR-01070151", "TCL-ERR-01220002"],
    },
    {
        "manufacturer_slug": "f5",
        "title": "BIG-IP DSC Device Trust, Sync Groups, and Connection Mirroring",
        "description": "Configure BIG-IP Device Service Clustering (DSC) for Active-Standby and Active-Active. Trust domains, sync-failover groups, connection mirroring, and Global Traffic Manager failover.",
        "source_url": "https://techdocs.f5.com/en-us/bigip-17-1-0/big-ip-device-service-clustering-administration.html",
        "tags": ["f5", "big-ip", "dsc", "ha", "config-sync", "failover"],
        "scenario_type": "integration",
        "error_codes": ["DSC-01071CB0", "DSC-TRUST-0107176F"],
    },

    # ── HPE (6) ───────────────────────────────────────────────
    {
        "manufacturer_slug": "hpe",
        "title": "iLO 5 Factory Reset via Auxiliary Power — Unresponsive BMC Recovery",
        "description": "Recover an unresponsive iLO 5 BMC on ProLiant Gen10/Gen10+ servers. Covers the physical iLO reset button procedure, CLI `cd /map1` reset via virtual serial, and preserving user accounts when forcing a full cold reset via the system maintenance switch.",
        "source_url": "https://support.hpe.com/hpesc/public/docDisplay?docId=a00105236en_us",
        "tags": ["hpe", "ilo5", "bmc", "proliant", "gen10", "reset"],
        "scenario_type": "troubleshooting",
        "error_codes": ["ILO-0x0005", "ILO-EVT-8217", "ILO-BMC-UNRESPONSIVE"],
    },
    {
        "manufacturer_slug": "hpe",
        "title": "iLO 5 HTTPS Certificate Expiration — Renewal and Remote Access Recovery",
        "description": "Restore HTTPS access to iLO 5 after a certificate expires. Covers CSR generation with proper iDevID SANs, import of an internal CA-signed cert via XML/RIBCL, regeneration of the self-signed fallback, and browser trust store updates for bulk-managed fleets.",
        "source_url": "https://support.hpe.com/hpesc/public/docDisplay?docId=c03298644",
        "tags": ["hpe", "ilo5", "ssl", "certificate", "ribcl", "https"],
        "scenario_type": "troubleshooting",
        "error_codes": ["ILO-CERT-0x0038", "ERR_CERT_DATE_INVALID", "RIBCL-E-0013"],
    },
    {
        "manufacturer_slug": "hpe",
        "title": "HPE OneView Server Profile Compliance Drift — Remediation Workflow",
        "description": "Diagnose and remediate Server Profile non-compliance in HPE OneView 5.x/6.x. Profile vs template diff inspection, firmware baseline updates, SAN connection remapping, and scheduling ordered compliance runs to avoid simultaneous reboots across an enclosure.",
        "source_url": "https://techhub.hpe.com/eginfolib/synergy/6.0/s/online-help/GUID-5A7F94A6-2A4C-4F9E-9141-B8C65F2FAAC0.html",
        "tags": ["hpe", "oneview", "server-profile", "compliance", "synergy", "c7000"],
        "scenario_type": "troubleshooting",
        "error_codes": ["OV-PROFILE-NONCOMPLIANT", "OV-FW-BASELINE-4017", "OV-SAS-4103"],
    },
    {
        "manufacturer_slug": "hpe",
        "title": "HPE MSA 2060 Controller Failover and SAS Cabling Path Validation",
        "description": "Troubleshoot controller failover on MSA 2060/2062 arrays. Identify stuck-owner volumes, force-failback via SMU, validate SAS expander connectivity with `show enclosures`, and interpret LED blink codes during controller firmware updates.",
        "source_url": "https://support.hpe.com/hpesc/public/docDisplay?docId=sd00002122en_us",
        "tags": ["hpe", "msa", "msa2060", "storage", "sas", "failover"],
        "scenario_type": "troubleshooting",
        "error_codes": ["MSA-A0BC0001", "MSA-SAS-LINK-DOWN", "MSA-CTLR-FAILOVER-A205"],
    },
    {
        "manufacturer_slug": "hpe",
        "title": "HPE Nimble Storage Group Leader Failover and Volume Resync",
        "description": "Handle Group Leader failover in Nimble Storage arrays. Covers split-brain detection, `group --promote` from the NimbleOS CLI, volume collection resync after partial network partition, and validating replication lag before re-enabling scheduled snapshots.",
        "source_url": "https://infosight.hpe.com/InfoSight/media/cms/active/public/pubs_NimbleOS_6_1_1_Administration_Guide.pdf",
        "tags": ["hpe", "nimble", "storage", "replication", "group-leader", "failover"],
        "scenario_type": "troubleshooting",
        "error_codes": ["NIMBLE-EVT-2000", "NIMBLE-REPL-LAG-3107", "NIMBLE-GL-SPLITBRAIN"],
    },
    {
        "manufacturer_slug": "hpe",
        "title": "HPE Service Pack for ProLiant (SPP) Offline Firmware Flash Procedure",
        "description": "Perform an offline firmware upgrade using HPE SPP on ProLiant Gen10+. USB key preparation with SUM, interactive vs automatic modes, baseline creation for fleet-wide rollout via OneView, and rollback strategy when a BIOS revision introduces regressions.",
        "source_url": "https://support.hpe.com/hpesc/public/docDisplay?docId=a00094257en_us",
        "tags": ["hpe", "spp", "firmware", "sum", "proliant", "offline-update"],
        "scenario_type": "migration",
        "error_codes": ["SPP-SUM-E1078", "SPP-BASELINE-MISMATCH", "SPP-0x40"],
    },

    # ── Aruba (6) ─────────────────────────────────────────────
    {
        "manufacturer_slug": "aruba",
        "title": "ClearPass 802.1X Authentication Failure — Certificate Chain Debug",
        "description": "Root-cause 802.1X auth failures in ClearPass Policy Manager. Access Tracker drill-down, RADIUS attribute inspection, EAP-TLS cert chain validation (intermediate CA trust issues), and NAD shared-secret mismatch detection via `tcpdump` on the CPPM internal interface.",
        "source_url": "https://www.arubanetworks.com/techdocs/ClearPass/6.11/PolicyManager/Content/CPPM_UserGuide/Admin/AccessTracker.htm",
        "tags": ["aruba", "clearpass", "802.1x", "radius", "eap-tls", "authentication"],
        "scenario_type": "troubleshooting",
        "error_codes": ["CPPM-RADIUS-REJECT", "CPPM-EAP-TLS-4013", "CPPM-ERR-1201"],
    },
    {
        "manufacturer_slug": "aruba",
        "title": "ClearPass OnGuard Posture Failure — Agent Troubleshooting",
        "description": "Diagnose OnGuard posture check failures: persistent vs dissolvable agent mismatch, missing SHV plugins, Windows Security Center API blocked by GPO, and the remediation VLAN redirect loop when the agent cannot reach the CPPM update server.",
        "source_url": "https://www.arubanetworks.com/techdocs/ClearPass/6.11/PolicyManager/Content/CPPM_UserGuide/OnGuard/OnGuardAgents.htm",
        "tags": ["aruba", "clearpass", "onguard", "nac", "posture", "remediation"],
        "scenario_type": "troubleshooting",
        "error_codes": ["ONGUARD-2041", "ONGUARD-SHV-MISSING", "CPPM-POSTURE-UNHEALTHY"],
    },
    {
        "manufacturer_slug": "aruba",
        "title": "Aruba Instant AP Cluster Firmware Upgrade and Mesh Rollback",
        "description": "Upgrade a mesh Instant AP cluster without service outage. Virtual Controller failover during image swap, auto-rollback behavior on mesh-point-to-portal disconnect, and recovery from a split-brain cluster after a partial image push via AirWave.",
        "source_url": "https://www.arubanetworks.com/techdocs/Instant_88_X/HTML/Content/instant-ug/upgrades/instant-ap-upgrade.htm",
        "tags": ["aruba", "instant-ap", "mesh", "firmware", "airwave", "upgrade"],
        "scenario_type": "migration",
        "error_codes": ["IAP-UPGRADE-305", "IAP-MESH-PORTAL-LOST", "IAP-VC-FAILOVER"],
    },
    {
        "manufacturer_slug": "aruba",
        "title": "AOS-CX VSX Split-Brain Recovery — ISL Failure Scenarios",
        "description": "Recover from VSX split-brain on AOS-CX 10.x. ISL (Inter-Switch Link) keepalive vs data link separation, forced secondary role demotion, LAG member pruning during asymmetric failure, and configuration sync repair via `vsx sync` without rebooting active links.",
        "source_url": "https://www.arubanetworks.com/techdocs/AOS-CX/10.11/HTML/high_availability/Content/Chp_VSX/vsx.htm",
        "tags": ["aruba", "aos-cx", "vsx", "split-brain", "isl", "ha"],
        "scenario_type": "troubleshooting",
        "error_codes": ["VSX-ISL-DOWN", "VSX-SPLIT-BRAIN", "VSX-SYNC-ERR-2104"],
    },
    {
        "manufacturer_slug": "aruba",
        "title": "Aruba Central Cloud Onboarding — ZTP and TPM Chain Validation",
        "description": "Onboard Aruba CX switches and APs to Aruba Central via Zero-Touch Provisioning. TPM attestation failure diagnosis, Activate account claim conflicts, DHCP option 60/43 requirements, and manual device claim when the factory-default ZTP loop cannot reach the cloud.",
        "source_url": "https://www.arubanetworks.com/techdocs/central/latest/content/nms/device-onbrd/ztp.htm",
        "tags": ["aruba", "central", "ztp", "onboarding", "tpm", "activate"],
        "scenario_type": "integration",
        "error_codes": ["CENTRAL-ZTP-1301", "ACTIVATE-CLAIM-CONFLICT", "TPM-ATTEST-FAIL"],
    },
    {
        "manufacturer_slug": "aruba",
        "title": "ClearPass Guest Self-Registration with SMS Sponsor Approval",
        "description": "Configure Guest self-registration with SMS OTP and sponsor approval. SMS gateway integration (Twilio, Nexmo), custom landing pages with Skins, sponsor lookup via AD group membership, and handling OTP delivery failures via secondary email fallback.",
        "source_url": "https://www.arubanetworks.com/techdocs/ClearPass/6.11/Guest/Content/Home.htm",
        "tags": ["aruba", "clearpass", "guest", "sms", "otp", "sponsor"],
        "scenario_type": "integration",
        "error_codes": ["GUEST-SMS-DELIVERY-FAIL", "GUEST-SPONSOR-TIMEOUT", "HTTP-429"],
    },

    # ── Dell (6) ──────────────────────────────────────────────
    {
        "manufacturer_slug": "dell",
        "title": "iDRAC9 Lifecycle Controller Firmware Rollback via Web UI",
        "description": "Roll back a failed iDRAC9 / LC firmware update on PowerEdge 14G/15G. Navigate to the LC rollback menu, identify the previous known-good image, and handle the case where the running firmware is corrupted by using the RACADM `fwupdate` recovery over local console.",
        "source_url": "https://www.dell.com/support/manuals/en-us/idrac9-lifecycle-controller-v4.x-series/idrac9_4.00.00.00_ug",
        "tags": ["dell", "idrac9", "lifecycle-controller", "firmware", "rollback", "poweredge"],
        "scenario_type": "troubleshooting",
        "error_codes": ["IDRAC-SUP0516", "IDRAC-RED128", "LC-FW-ROLLBACK-FAIL"],
    },
    {
        "manufacturer_slug": "dell",
        "title": "PowerEdge R750 Backplane PCIe Slot Mapping and Replacement",
        "description": "Replace the front backplane on R750 without losing slot-to-drive mapping. PERC H755 foreign config preservation, NVMe vs SAS/SATA backplane variants, cable routing verification against the service manual, and post-install consistency check via `omreport storage pdisk`.",
        "source_url": "https://www.dell.com/support/manuals/en-us/poweredge-r750/per750_ism_pub",
        "tags": ["dell", "poweredge", "r750", "backplane", "perc", "hardware"],
        "scenario_type": "troubleshooting",
        "error_codes": ["PDR1016", "CPU0000", "PERC-FOREIGN-CFG-DETECTED"],
    },
    {
        "manufacturer_slug": "dell",
        "title": "OpenManage Enterprise — SNMPv3 and Redfish Device Discovery",
        "description": "Onboard PowerEdge servers and network switches into OpenManage Enterprise (OME) 4.x. Discovery profiles with SNMPv3 auth + priv, Redfish API credential vaulting, discovery job throttling to avoid iDRAC lockout, and remediating failed inventory on older 13G hardware.",
        "source_url": "https://www.dell.com/support/manuals/en-us/dell-openmanage-enterprise/ome_4.0_ug",
        "tags": ["dell", "openmanage", "ome", "snmp", "redfish", "discovery"],
        "scenario_type": "integration",
        "error_codes": ["OME-DISC-4091", "REDFISH-401", "SNMP-V3-AUTH-FAIL"],
    },
    {
        "manufacturer_slug": "dell",
        "title": "Dell PERC H755 Rebuild Priority and Foreign Configuration Import",
        "description": "Manage RAID rebuilds on PERC H755 controllers. Rebuild rate tuning to balance host I/O, foreign config preview and safe import after chassis swap, patrol read schedule, and interpreting the `Unconfigured Good` vs `Foreign` disk states in iDRAC Storage.",
        "source_url": "https://www.dell.com/support/manuals/en-us/poweredge-rc-h755/perc11_ug",
        "tags": ["dell", "perc", "h755", "raid", "rebuild", "foreign-config"],
        "scenario_type": "troubleshooting",
        "error_codes": ["PERC-FOREIGN-CFG", "PERC-REBUILD-FAILED", "PDR64"],
    },
    {
        "manufacturer_slug": "dell",
        "title": "iDRAC9 Virtual Console Certificate Renewal — Java and HTML5 Clients",
        "description": "Renew the iDRAC9 web and virtual console certificate. CSR attributes for proper SAN/CN matching, PKCS#12 upload via RACADM, handling Java plugin deprecation by switching the default console to eHTML5, and bulk rollout via the iDRAC Service Module and Ansible collection.",
        "source_url": "https://infohub.delltechnologies.com/l/security-configuration-guide-integrated-dell-remote-access-controller-9-idrac9-idrac9/ssl-certificate-management/",
        "tags": ["dell", "idrac9", "certificate", "virtual-console", "racadm", "html5"],
        "scenario_type": "hardening",
        "error_codes": ["IDRAC-SEC0512", "RACADM-ERR-CERT-CHAIN", "ERR_CERT_COMMON_NAME_INVALID"],
    },
    {
        "manufacturer_slug": "dell",
        "title": "Dell PowerStore T — Volume Creation, Host Mapping, and Async Replication",
        "description": "Provision volumes on PowerStore T appliances. Volume groups for application-consistent snapshots, host initiator mapping via iSCSI vs NVMe/TCP, remote system pairing for asynchronous replication, and RPO tuning via replication schedule + MTU validation on the replication network.",
        "source_url": "https://www.dell.com/support/manuals/en-us/powerstore-1000t/pwrstr-cfghost",
        "tags": ["dell", "powerstore", "storage", "replication", "iscsi", "nvme-tcp"],
        "scenario_type": "integration",
        "error_codes": ["PS-REPL-0x2104", "PS-HOST-INIT-MISMATCH", "PS-RPO-EXCEEDED"],
    },

    # ══════════════════════════════════════════════════════════
    #  NEW BATCH · Splunk (5)
    # ══════════════════════════════════════════════════════════
    {
        "manufacturer_slug": "splunk",
        "title": "Splunk OTEL Collector for VMware vSphere — Metrics Pipeline Setup",
        "description": "Deploy the Splunk Distribution of OpenTelemetry Collector to scrape vCenter metrics via the vmware receiver. Covers SDDC credentials scoping, govmomi connection pool sizing for 500+ host inventories, metric filtering to stay under the 1M DPM ingest budget, and TLS cert pinning to vCenter's internal CA.",
        "source_url": "https://docs.splunk.com/observability/en/gdi/opentelemetry/components/vmware-receiver.html",
        "tags": ["splunk", "otel", "vmware", "vcenter", "observability", "metrics"],
        "scenario_type": "integration",
        "error_codes": ["SPL-OTEL-1001", "OTEL-VMW-AUTH-FAIL", "GOVMOMI-INVALID-LOGIN"],
    },
    {
        "manufacturer_slug": "splunk",
        "title": "OTEL Collector on Bare-Metal Linux — systemd, hostmetrics, cgroup v2",
        "description": "Install otelcol-contrib on RHEL 9 / Ubuntu 22.04 bare-metal hosts. systemd unit hardening (ProtectSystem, CapabilityBoundingSet), hostmetrics receiver with cgroup v2 awareness, filelog receiver positions file on XFS, and batching tuned for 10k events/sec to avoid backpressure on the splunk_hec exporter.",
        "source_url": "https://docs.splunk.com/observability/en/gdi/opentelemetry/install-linux.html",
        "tags": ["splunk", "otel", "linux", "bare-metal", "systemd", "hostmetrics"],
        "scenario_type": "hardening",
        "error_codes": ["SPL-OTEL-2014", "OTEL-EXPORTER-TIMEOUT", "SYSTEMD-203"],
    },
    {
        "manufacturer_slug": "splunk",
        "title": "Universal Forwarder Tuning on Citrix VDAs — I/O and CPU Ceiling",
        "description": "Tame Universal Forwarder resource use on Citrix Virtual Apps/Desktops. maxKBps throttle per pipeline, thruput limits under PVS/MCS image contention, read-only mounted forwarder path to survive vDisk resets, and excluding WEM/FSLogix noise with whitelisted EventCode filters.",
        "source_url": "https://docs.splunk.com/Documentation/Forwarder/latest/Forwarder/Configureaggregatorprocessor",
        "tags": ["splunk", "universal-forwarder", "citrix", "vda", "pvs", "tuning"],
        "scenario_type": "hardening",
        "error_codes": ["SPL-UF-3008", "UF-THRUPUT-BLOCKED", "UF-PARSING-QUEUE-FULL"],
    },
    {
        "manufacturer_slug": "splunk",
        "title": "HEC Indexer Discovery and Load Balancing for OTEL Exporters",
        "description": "Replace static HEC endpoints with indexer discovery. Cluster Manager ACK settings, splunk_hec exporter retry_on_failure + queue_size sizing, indexer acknowledgment end-to-end, and detection of event loss during indexer rolling restarts via the pipeline metrics queue.",
        "source_url": "https://docs.splunk.com/observability/en/gdi/opentelemetry/components/splunk-hec-exporter.html",
        "tags": ["splunk", "hec", "otel", "indexer-discovery", "load-balancing"],
        "scenario_type": "integration",
        "error_codes": ["SPL-HEC-4010", "HEC-ACK-TIMEOUT", "HTTP-503"],
    },
    {
        "manufacturer_slug": "splunk",
        "title": "Splunk ITSI Glass Tables from OTEL Signals — KPI Wiring",
        "description": "Wire OTEL metrics into ITSI service trees. metric_type mapping gauge vs counter, KPI thresholds with adaptive baselines, entity import via CSV lookup synced from vCenter, and avoiding KPI flapping via dataPointsReq / frequency tuning on noisy services.",
        "source_url": "https://docs.splunk.com/Documentation/ITSI/latest/User/AboutITSI",
        "tags": ["splunk", "itsi", "otel", "kpi", "glass-tables", "service-tree"],
        "scenario_type": "integration",
        "error_codes": ["SPL-ITSI-5021", "ITSI-KPI-NO-DATA", "ITSI-ENTITY-IMPORT-FAIL"],
    },

    # ══════════════════════════════════════════════════════════
    #  NEW BATCH · Citrix (5)
    # ══════════════════════════════════════════════════════════
    {
        "manufacturer_slug": "citrix",
        "title": "Citrix Cloud API — Bearer Token Rotation and Rate Limit Handling",
        "description": "Authenticate against Citrix Cloud REST API via customer / client ID + secret. Token lifetime (1h) refresh strategy, X-RateLimit header back-off, scoping to specific Delivery Groups, and rotating client secrets without service account downtime via overlapping credentials.",
        "source_url": "https://developer.cloud.com/citrix-cloud/citrix-cloud-api-overview/docs/get-started-with-citrix-cloud-apis",
        "tags": ["citrix", "citrix-cloud", "api", "oauth", "rate-limit"],
        "scenario_type": "integration",
        "error_codes": ["CTX-API-401", "CTX-API-429", "CTX-TOKEN-EXPIRED"],
    },
    {
        "manufacturer_slug": "citrix",
        "title": "Citrix Monitor OData API — Session Telemetry for Splunk Ingest",
        "description": "Pull session, connection failure, and ICA RTT metrics via the Monitor OData v4 endpoint. Delta queries with $deltatoken, page chunking on 7-day history windows, joining SessionV2 with MachineV2, and mapping to Splunk CIM Authentication datamodel.",
        "source_url": "https://developer-docs.citrix.com/projects/monitor-service-odata-api/en/latest/",
        "tags": ["citrix", "monitor", "odata", "telemetry", "splunk", "cim"],
        "scenario_type": "integration",
        "error_codes": ["CTX-ODATA-400", "CTX-ODATA-DELTATOKEN-EXPIRED", "CTX-MON-SESSION-LOST"],
    },
    {
        "manufacturer_slug": "citrix",
        "title": "NSX-T Edge Node Metrics via Splunk OTEL — prometheusreceiver Wiring",
        "description": "Scrape NSX-T Edge Node /stats endpoints using OTEL prometheusreceiver. Enable Prometheus exporter on Edge Transport Nodes, TLS with NSX Manager principal identity cert, label rewriting for transport_node name, and Tier-0 / Tier-1 routing dashboards in Splunk O11y Cloud.",
        "source_url": "https://docs.vmware.com/en/VMware-NSX/4.1/administration/GUID-nsx-prometheus.html",
        "tags": ["citrix", "nsx-t", "edge", "prometheus", "otel", "metrics"],
        "scenario_type": "integration",
        "error_codes": ["NSX-EDGE-STATS-503", "OTEL-PROM-SCRAPE-FAIL", "NSX-PI-CERT-INVALID"],
    },
    {
        "manufacturer_slug": "citrix",
        "title": "Citrix ADC (NetScaler) AppFlow to Splunk — HDX Insight Export",
        "description": "Enable AppFlow on Citrix ADC for HDX Insight. IPFIX template negotiation, collector redundancy with ha-peer on Splunk Stream, parsing ICA latency + L7 latency fields into Splunk, and throttling AppFlow on VPX instances to avoid management CPU saturation.",
        "source_url": "https://docs.netscaler.com/en-us/citrix-adc/current-release/ns-ag-appflow-intro-wrapper-con.html",
        "tags": ["citrix", "adc", "netscaler", "appflow", "hdx-insight", "ipfix"],
        "scenario_type": "integration",
        "error_codes": ["NS-APPFLOW-TEMPLATE-FAIL", "NS-IPFIX-COLLECTOR-DOWN", "NS-CPU-HIGH-4403"],
    },
    {
        "manufacturer_slug": "citrix",
        "title": "FSLogix Profile Container Corruption — VHDX Repair on Citrix VDAs",
        "description": "Diagnose and recover corrupted FSLogix profile containers. Event ID 26 / 52 differentiation, offline VHDX mount via diskpart, ProfileType=3 read-only fallback during remediation, and detecting Redirections.xml loops via FSLogix Frxsvc trace logging.",
        "source_url": "https://learn.microsoft.com/en-us/fslogix/troubleshooting-events-errors",
        "tags": ["citrix", "fslogix", "vhdx", "profile", "vda", "troubleshooting"],
        "scenario_type": "troubleshooting",
        "error_codes": ["FSLOGIX-26", "FSLOGIX-52", "FRXSVC-31009", "0x0000003B"],
    },
]


ACADEMY: list[dict] = [
    {"certification": "VCP",   "level": "associate",    "title": "VCP-DCV 2024 — vSphere 8 Official Exam Prep",          "description": "VMware official study guide with practice exams, Hands-on Labs, and blueprint mapping for VCP Data Center Virtualization.", "resource_url": "https://www.vmware.com/learning/certification/vcp-dcv.html", "is_free": True,  "tags": ["vsphere", "vcenter", "esxi"]},
    {"certification": "VCP",   "level": "professional", "title": "VCAP-DCV Design 3V0-624",                              "description": "Advanced design exam: vSphere architecture decisions, availability design, capacity planning, and performance optimization scenarios.", "resource_url": "https://www.vmware.com/learning/certification/vcap-dcv-design.html", "is_free": False, "tags": ["design", "architecture", "vcap"]},
    {"certification": "CCNA",  "level": "beginner",     "title": "Cisco Networking Basics — Free NetAcad Course",        "description": "Entry-level: OSI model, IP addressing, subnetting, basic switching, and intro to routing.", "resource_url": "https://www.netacad.com/courses/networking-basics", "is_free": True,  "tags": ["fundamentals", "osi", "ip", "subnetting"]},
    {"certification": "CCNA",  "level": "associate",    "title": "Cisco CCNA 200-301 — Full Study Guide",                "description": "Comprehensive: networking fundamentals, IP services, security basics, and automation.", "resource_url": "https://www.netacad.com/courses/ccna", "is_free": True,  "tags": ["routing", "switching", "ospf", "vlans"]},
    {"certification": "CCNP",  "level": "professional", "title": "CCNP Enterprise ENCOR 350-401",                        "description": "Deep dive into enterprise infrastructure, SD-WAN, QoS, wireless, and network assurance.", "resource_url": "https://www.cisco.com/c/en/us/training-events/training-certifications/certifications/professional/ccnp-enterprise.html", "is_free": False, "tags": ["sd-wan", "bgp", "qos", "wireless"]},
    {"certification": "CCIE",  "level": "expert",       "title": "CCIE Enterprise Infrastructure v1.1 Lab Prep",         "description": "Advanced lab prep: Segment Routing, EVPN/VXLAN, MPLS TE, and SD-WAN design at scale.", "resource_url": "https://www.cisco.com/c/en/us/training-events/training-certifications/certifications/expert/ccie-enterprise-infrastructure.html", "is_free": False, "tags": ["mpls", "segment-routing", "evpn", "vxlan"]},
    {"certification": "CISSP", "level": "professional", "title": "CISSP Official Study Guide 9th Edition",                "description": "ISC2 official material covering all 8 CBK domains.", "resource_url": "https://www.isc2.org/certifications/cissp", "is_free": False, "tags": ["security", "iam", "cryptography", "risk"]},
    {"certification": "CEH",   "level": "professional", "title": "CEH v12 — Certified Ethical Hacker",                    "description": "EC-Council official courseware: penetration testing, vulnerability analysis, exploit development.", "resource_url": "https://www.eccouncil.org/train-certify/certified-ethical-hacker-ceh/", "is_free": False, "tags": ["pentest", "vulnerability", "kali", "exploitation"]},
    {"certification": "PCNSA", "level": "associate",    "title": "Palo Alto PCNSA Study Guide",                          "description": "Prepare for the Palo Alto Networks PCNSA exam with real-world scenarios.", "resource_url": "https://www.paloaltonetworks.com/services/education/certification", "is_free": True,  "tags": ["palo-alto", "ngfw", "pan-os", "security"]},
    {"certification": "NSE4",  "level": "associate",    "title": "Fortinet NSE 4 — FortiGate Security",                  "description": "NSE4 certification prep covering FortiGate administration, security profiles, SSL-VPN, and SD-WAN.", "resource_url": "https://training.fortinet.com/local/staticpage/view.php?page=certifications", "is_free": True,  "tags": ["fortinet", "fortigate", "vpn", "ips"]},
]


EXTRA_CERT_ENUM_VALUES: list[str] = ["PCNSA", "NSE4"]
