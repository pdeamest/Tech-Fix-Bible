-- scripts/seed_kb_articles.sql
-- Seeds 8 demo KB articles using manufacturer slugs (idempotent).
-- Re-runnable: skips articles whose source_url already exists.

BEGIN;

-- vmware
INSERT INTO knowledge_base (manufacturer_id, title, description, source_url, tags, status)
SELECT id,
  'vSphere HA Cluster — Heartbeat Datastores & Admission Control',
  'Configure vSphere High Availability with heartbeat datastores, host monitoring levels, VM restart priorities, and admission control policies to guarantee failover capacity in mixed-workload clusters.',
  'https://docs.vmware.com/en/VMware-vSphere/8.0/vsphere-availability/GUID-5432CA22-F8F0-409E-8B5A-D2D8F9F8E0D3.html',
  ARRAY['vsphere','ha','cluster','esxi','vcenter'],
  'online'::link_status
FROM manufacturers WHERE slug='vmware'
ON CONFLICT DO NOTHING;

INSERT INTO knowledge_base (manufacturer_id, title, description, source_url, tags, status)
SELECT id,
  'NSX-T Micro-segmentation with Distributed Firewall',
  'Implement zero-trust micro-segmentation using NSX-T distributed firewall rules. Tag-based policy creation, workload grouping by OS/app tier, east-west traffic inspection, and Identity Firewall for AD users.',
  'https://docs.vmware.com/en/VMware-NSX/4.1/administration/GUID-6AB240DB-949C-4E95-A9A7-4AC6EF5E3036.html',
  ARRAY['nsx-t','micro-segmentation','dfw','zero-trust','security'],
  'online'::link_status
FROM manufacturers WHERE slug='vmware'
ON CONFLICT DO NOTHING;

-- cisco
INSERT INTO knowledge_base (manufacturer_id, title, description, source_url, tags, status)
SELECT id,
  'OSPF Area Types — Stub, NSSA, Totally Stubby Explained',
  'Detailed comparison of OSPF area types with IOS-XE configuration examples. Explains LSA filtering per type, default route injection, and design recommendations for enterprise topologies.',
  'https://www.cisco.com/c/en/us/support/docs/ip/open-shortest-path-first-ospf/13703-8.html',
  ARRAY['ospf','routing','ios-xe','area','lsa'],
  'online'::link_status
FROM manufacturers WHERE slug='cisco'
ON CONFLICT DO NOTHING;

INSERT INTO knowledge_base (manufacturer_id, title, description, source_url, tags, status)
SELECT id,
  'BGP Route Filtering — Prefix Lists, Route Maps & Communities',
  'Granular BGP route filtering using prefix lists combined with route maps. Inbound/outbound filter examples, conditional advertisements, community tagging, and LOCAL_PREF tuning for path selection.',
  'https://www.cisco.com/c/en/us/support/docs/ip/border-gateway-protocol-bgp/13753-25.html',
  ARRAY['bgp','routing','prefix-list','route-map','communities'],
  'online'::link_status
FROM manufacturers WHERE slug='cisco'
ON CONFLICT DO NOTHING;

-- paloalto
INSERT INTO knowledge_base (manufacturer_id, title, description, source_url, tags, status)
SELECT id,
  'Security Zones Architecture and Policy Rulebase Design',
  'Design a robust security policy using Palo Alto security zones. Zone types (tap, L2, L3, virtual wire), inter-zone policies, Security Profile Groups, and rulebase ordering for optimal performance.',
  'https://docs.paloaltonetworks.com/pan-os/11-0/pan-os-admin/policy/security-zones',
  ARRAY['palo-alto','zones','security-policy','ngfw','rulebase'],
  'online'::link_status
FROM manufacturers WHERE slug='paloalto'
ON CONFLICT DO NOTHING;

-- fortinet
INSERT INTO knowledge_base (manufacturer_id, title, description, source_url, tags, status)
SELECT id,
  'FortiGate SD-WAN Performance SLA and Traffic Steering Rules',
  'Configure SD-WAN performance SLA probes (latency, jitter, packet loss) and traffic steering rules. Load balancing algorithms: weighted, spillover, best quality, lowest cost, and custom rule-based steering.',
  'https://docs.fortinet.com/document/fortigate/7.4.0/administration-guide/sd-wan',
  ARRAY['fortinet','sd-wan','performance-sla','traffic-steering'],
  'online'::link_status
FROM manufacturers WHERE slug='fortinet'
ON CONFLICT DO NOTHING;

-- checkpoint
INSERT INTO knowledge_base (manufacturer_id, title, description, source_url, tags, status)
SELECT id,
  'SmartConsole Policy Layers, Inline Layers, and Installation',
  'Manage security policies in Check Point SmartConsole R81.20. Policy layer architecture, inline layers for granular control, desktop security policies, and optimizing installation time on large gateways.',
  'https://sc1.checkpoint.com/documents/R81.20/WebAdminGuides/EN/CP_R81.20_SecurityManagement_AdminGuide/Default.htm',
  ARRAY['checkpoint','smartconsole','policy','layers','r81'],
  'online'::link_status
FROM manufacturers WHERE slug='checkpoint'
ON CONFLICT DO NOTHING;

-- juniper
INSERT INTO knowledge_base (manufacturer_id, title, description, source_url, tags, status)
SELECT id,
  'JunOS MPLS LDP and RSVP-TE Traffic Engineering on MX Series',
  'Configure MPLS with LDP and RSVP-TE on MX Series. LSP path creation, CSPF-based computation, Fast Reroute (FRR) with link/node protection, and MPLS OAM tools (ping, traceroute).',
  'https://www.juniper.net/documentation/us/en/software/junos/mpls/topics/topic-map/mpls-overview.html',
  ARRAY['junos','mpls','ldp','rsvp','traffic-engineering'],
  'online'::link_status
FROM manufacturers WHERE slug='juniper'
ON CONFLICT DO NOTHING;

COMMIT;

-- Verification
SELECT m.slug, COUNT(*) AS articles
FROM knowledge_base kb
JOIN manufacturers m ON m.id = kb.manufacturer_id
GROUP BY m.slug
ORDER BY m.slug;
