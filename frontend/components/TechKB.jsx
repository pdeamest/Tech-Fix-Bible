import { useState, useMemo, useEffect, useRef } from "react";
import { Search, ThumbsUp, ThumbsDown, ExternalLink, BookOpen, X, Award, Wifi, WifiOff, AlertCircle, ChevronRight, Layers, Database, Shield, Play, CheckCircle2, Loader2, Terminal, KeyRound, LogOut, Server, FileText, Bug, TrendingUp, BarChart3 } from "lucide-react";

const C = {
  bg:'#0d1117',surface:'#161b22',surface2:'#1c2128',hover:'#21262d',
  border:'#30363d',border2:'#444c56',t0:'#e6edf3',t1:'#8b949e',t2:'#6e7681',
  blue:'#58a6ff',blueD:'#1f6feb',green:'#3fb950',red:'#f85149',
  amber:'#d29922',purple:'#bc8cff',teal:'#2ea043',
};
const mono="ui-monospace,'Cascadia Code','SF Mono','Fira Code',monospace";
const sans="ui-sans-serif,system-ui,-apple-system,sans-serif";

const T={
  en:{tagline:'Technical Knowledge Base',search:'Search articles, vendors, error codes, topics…',kb:'Knowledge Base',academy:'Academy',admin:'Admin',
    allVendors:'All vendors',allStatuses:'All statuses',online:'Online',broken:'Broken link',unchecked:'Unchecked',
    votes:'votes',helpful:'Helpful',notHelpful:'Not helpful',resolved:'resolved',noResults:'No articles found. Try different keywords.',
    viewDocs:'View official docs',certResources:'Certification Resources',allCerts:'All certifications',allLevels:'All levels',
    free:'Free',paid:'Paid',beginner:'Beginner',associate:'Associate',professional:'Professional',expert:'Expert',
    resolution:'Resolution score',articles:'articles',loginVote:'Demo — votes tracked locally',
    onlyErrors:'Only errors',errorCodePlaceholder:'Exact code (e.g. FSLOGIX-26)',errorCodes:'Error codes',scenario:'Scenario',
    topCodes:'Top Error Codes',topCodesDesc:'Most frequent codes across the knowledge base',clickToFilter:'Click any code to filter',
    uniqueCodes:'unique',totalUses:'uses',withCodes:'articles with codes',filterCleared:'Filter cleared',filtering:'Filtering by',
    adminPanel:'Admin Panel',adminSub:'Trigger ingestion and link validation on the platform.',
    adminGate:'Admin access',adminGateHint:'Paste your JWT (any value works in this demo).',authenticate:'Authenticate',
    signOut:'Sign out',seedDb:'Seed database',seedDesc:'Idempotent upsert of manufacturers, KB articles and Academy resources.',
    runHealth:'Run link health check',healthDesc:'Parallel HEAD requests across all source URLs.',
    dryRun:'Dry-run',run:'Run',running:'Running…',console:'Console',clearLogs:'Clear',
    lastRun:'Last run',duration:'Duration',vendors:'Vendors',kbArticles:'KB articles',academyRes:'Academy resources',
    inserted:'inserted',updated:'updated',noRunsYet:'No runs yet. Trigger an action above.'},
  es:{tagline:'Base de Conocimiento Técnica',search:'Buscar artículos, vendors, códigos de error, temas…',kb:'Base de Conocimiento',academy:'Academia',admin:'Admin',
    allVendors:'Todos los vendors',allStatuses:'Todos los estados',online:'En línea',broken:'Enlace roto',unchecked:'Sin verificar',
    votes:'votos',helpful:'Útil',notHelpful:'No fue útil',resolved:'resuelto',noResults:'Sin resultados. Intenta otras palabras.',
    viewDocs:'Ver documentación oficial',certResources:'Recursos de Certificación',allCerts:'Todas las certificaciones',allLevels:'Todos los niveles',
    free:'Gratis',paid:'De pago',beginner:'Principiante',associate:'Asociado',professional:'Profesional',expert:'Experto',
    resolution:'Puntuación de resolución',articles:'artículos',loginVote:'Demo — votos guardados localmente',
    onlyErrors:'Solo errores',errorCodePlaceholder:'Código exacto (ej. FSLOGIX-26)',errorCodes:'Códigos de error',scenario:'Escenario',
    topCodes:'Top Códigos de Error',topCodesDesc:'Códigos más frecuentes en la base de conocimiento',clickToFilter:'Click en un código para filtrar',
    uniqueCodes:'únicos',totalUses:'usos',withCodes:'artículos con códigos',filterCleared:'Filtro limpiado',filtering:'Filtrando por',
    adminPanel:'Panel de Administración',adminSub:'Dispara procesos de ingesta y verificación en la plataforma.',
    adminGate:'Acceso admin',adminGateHint:'Pega tu JWT (cualquier valor sirve en este demo).',authenticate:'Autenticar',
    signOut:'Cerrar sesión',seedDb:'Cargar base de datos',seedDesc:'Upsert idempotente de fabricantes, artículos KB y recursos Academy.',
    runHealth:'Verificar enlaces',healthDesc:'Peticiones HEAD en paralelo sobre todas las URLs fuente.',
    dryRun:'Modo simulación',run:'Ejecutar',running:'Ejecutando…',console:'Consola',clearLogs:'Limpiar',
    lastRun:'Última ejecución',duration:'Duración',vendors:'Fabricantes',kbArticles:'Artículos KB',academyRes:'Recursos Academy',
    inserted:'insertados',updated:'actualizados',noRunsYet:'Aún no hay ejecuciones. Dispara una acción arriba.'},
};

const VC = {vmware:'#1d6fa5',cisco:'#049fd9',paloalto:'#fa582d',fortinet:'#ee3124',checkpoint:'#d40f10',juniper:'#009f6b',f5:'#e4002b',aruba:'#ff8300',hpe:'#01a982',dell:'#007db8',splunk:'#e3451f',citrix:'#452170'};
const VN = {vmware:'VMware',cisco:'Cisco',paloalto:'Palo Alto',fortinet:'Fortinet',checkpoint:'Check Point',juniper:'Juniper',f5:'F5 Networks',aruba:'Aruba',hpe:'HPE',dell:'Dell',splunk:'Splunk',citrix:'Citrix'};

const ARTICLES=[
  {id:'1',mfr:'vmware',title:'vSphere HA Cluster — Heartbeat Datastores & Admission Control',description:'Configure vSphere High Availability with heartbeat datastores, host monitoring levels, VM restart priorities, and admission control policies.',tags:['vsphere','ha','cluster','esxi','vcenter'],status:'online',likes:54,dislikes:4,url:'https://docs.vmware.com/en/VMware-vSphere',scenario_type:'hardening',error_codes:['VMW-HA-2017','VMW-HA-1007','VMW-VC-1000095']},
  {id:'2',mfr:'vmware',title:'vSAN Stretched Cluster with Witness Host Appliance',description:'Deploy vSAN Stretched Cluster across two fault domains with a remote witness appliance.',tags:['vsan','stretched-cluster','witness','storage'],status:'online',likes:41,dislikes:6,url:'https://docs.vmware.com/en/VMware-vSAN',scenario_type:'integration',error_codes:['VSAN-60042','VSAN-60061','VSAN-WITNESS-1017']},
  {id:'3',mfr:'vmware',title:'NSX-T Micro-segmentation with Distributed Firewall',description:'Implement zero-trust micro-segmentation using NSX-T distributed firewall rules.',tags:['nsx-t','micro-segmentation','dfw','zero-trust','security'],status:'online',likes:67,dislikes:5,url:'https://docs.vmware.com/en/VMware-NSX',scenario_type:'hardening',error_codes:['NSX-DFW-1001','NSX-IDFW-3042']},
  {id:'4',mfr:'vmware',title:'vCenter LDAP / Active Directory SSO Identity Sources',description:'Integrate vCenter Server with Active Directory over LDAP for SSO.',tags:['vcenter','ldap','active-directory','sso','authentication'],status:'online',likes:38,dislikes:2,url:'https://docs.vmware.com/en/VMware-vSphere/8.0',scenario_type:'integration',error_codes:['VC-SSO-20003','VC-SSO-20117','LDAP-49','LDAP-81']},
  {id:'5',mfr:'cisco',title:'OSPF Area Types — Stub, NSSA, Totally Stubby Explained',description:'Detailed comparison of OSPF area types with IOS-XE configuration examples.',tags:['ospf','routing','ios-xe','area','lsa'],status:'online',likes:89,dislikes:7,url:'https://www.cisco.com/c/en/us/support/docs/ip/open-shortest-path-first-ospf',scenario_type:'reference',error_codes:['OSPF-4-ERRRCV','OSPF-4-CONFLICTING_LSAID','OSPF-5-ADJCHG']},
  {id:'6',mfr:'cisco',title:'BGP Route Filtering — Prefix Lists, Route Maps & Communities',description:'Granular BGP route filtering using prefix lists combined with route maps.',tags:['bgp','routing','prefix-list','route-map','communities'],status:'online',likes:103,dislikes:9,url:'https://www.cisco.com/c/en/us/support/docs/ip/border-gateway-protocol-bgp',scenario_type:'reference',error_codes:['BGP-3-NOTIFICATION','BGP-5-ADJCHANGE','BGP-4-MSGDUMP']},
  {id:'7',mfr:'cisco',title:'802.1Q Trunking, VTP Modes, and Native VLAN Security',description:'Configure IEEE 802.1Q trunking between Catalyst switches.',tags:['vlan','trunking','802.1q','vtp','switching'],status:'online',likes:71,dislikes:8,url:'https://www.cisco.com/c/en/us/support/docs/lan-switching/8021q',scenario_type:'hardening',error_codes:['VTP-4-VLANMODERR','DTP-4-TRUNKPORTCHG','SPANTREE-2-RECV_1Q_NON_TRUNK']},
  {id:'8',mfr:'cisco',title:'Catalyst 9000 RESTCONF API with Python Automation',description:'Automate Catalyst 9000 using RESTCONF with YANG models.',tags:['restconf','netconf','yang','python','automation','catalyst'],status:'broken',likes:44,dislikes:12,url:'https://developer.cisco.com/docs/ios-xe',scenario_type:'integration',error_codes:['HTTP-401','HTTP-409','YANG-MALFORMED-MSG','NETCONF-RPC-ERROR']},
  {id:'9',mfr:'paloalto',title:'Security Zones Architecture and Policy Rulebase Design',description:'Design a robust security policy using Palo Alto security zones.',tags:['palo-alto','zones','security-policy','ngfw','rulebase'],status:'online',likes:58,dislikes:3,url:'https://docs.paloaltonetworks.com/pan-os',scenario_type:'hardening',error_codes:['PAN-COMMIT-10001','PAN-POLICY-E0004']},
  {id:'10',mfr:'paloalto',title:'GlobalProtect VPN — Certificate Auth & HIP Check Policies',description:'Deploy GlobalProtect with internal/external gateways with HIP checks.',tags:['globalprotect','vpn','certificates','hip','prisma-access'],status:'online',likes:79,dislikes:5,url:'https://docs.paloaltonetworks.com/globalprotect',scenario_type:'integration',error_codes:['GP-E-1015','GP-E-1403','HIP-PROFILE-MISMATCH']},
  {id:'11',mfr:'paloalto',title:'Panorama Device Groups, Templates, and Config Inheritance',description:'Structure large-scale deployments using Panorama device groups and templates.',tags:['panorama','device-group','template','management'],status:'online',likes:62,dislikes:4,url:'https://docs.paloaltonetworks.com/panorama',scenario_type:'integration',error_codes:['PAN-PANORAMA-11003','PAN-TEMPLATE-CONFLICT-4020']},
  {id:'12',mfr:'fortinet',title:'FortiGate SD-WAN Performance SLA and Traffic Steering Rules',description:'Configure SD-WAN performance SLA probes and traffic steering rules.',tags:['fortinet','sd-wan','performance-sla','traffic-steering'],status:'online',likes:49,dislikes:6,url:'https://docs.fortinet.com/product/fortigate',scenario_type:'integration',error_codes:['FGT-SDWAN-0107','FGT-HEALTH-CHECK-FAIL']},
  {id:'13',mfr:'fortinet',title:'FortiAnalyzer ADOMs, Log Aggregation, and Report Automation',description:'Configure FortiAnalyzer as centralized log server with ADOMs.',tags:['fortianalyzer','logging','siem','adom','reports'],status:'online',likes:33,dislikes:5,url:'https://docs.fortinet.com/product/fortianalyzer',scenario_type:'integration',error_codes:['FAZ-ADOM-0902','FAZ-LOG-FORWARD-5001']},
  {id:'14',mfr:'fortinet',title:'FortiGate SSL-VPN with RADIUS and FortiToken MFA',description:'Deploy SSL-VPN with two-factor authentication via RADIUS + FortiToken Mobile.',tags:['fortigate','ssl-vpn','radius','mfa','fortitoken'],status:'online',likes:57,dislikes:7,url:'https://docs.fortinet.com/document/fortigate',scenario_type:'integration',error_codes:['FGT-SSLVPN-7026','FGT-AUTH-FAIL-0103','RADIUS-REJECT-28']},
  {id:'15',mfr:'checkpoint',title:'SmartConsole Policy Layers, Inline Layers, and Installation',description:'Manage security policies in Check Point SmartConsole R81.20.',tags:['checkpoint','smartconsole','policy','layers','r81'],status:'online',likes:41,dislikes:4,url:'https://sc1.checkpoint.com/documents/latest',scenario_type:'hardening',error_codes:['CP-POLICY-INSTALL-0201','CP-FWD-VERIFIER-1402']},
  {id:'16',mfr:'checkpoint',title:'ClusterXL Active-Active Load Sharing and Maestro HyperScale',description:'Deploy ClusterXL in Active-Active Load Sharing with CCP.',tags:['checkpoint','clusterxl','ha','load-sharing','maestro'],status:'broken',likes:28,dislikes:8,url:'https://sc1.checkpoint.com/documents/latest',scenario_type:'integration',error_codes:['CP-CLUSTER-101','CP-CCP-2307','CP-MAESTRO-6001']},
  {id:'17',mfr:'juniper',title:'JunOS MPLS LDP and RSVP-TE Traffic Engineering on MX Series',description:'Configure MPLS with LDP and RSVP-TE on MX Series.',tags:['junos','mpls','ldp','rsvp','traffic-engineering'],status:'online',likes:52,dislikes:6,url:'https://www.juniper.net/documentation',scenario_type:'reference',error_codes:['RPD-LDP-SESSION_DOWN','RPD-RSVP-PATHERR','RPD-MPLS-LSP-DOWN']},
  {id:'18',mfr:'juniper',title:'SRX Application-Level Gateways — SIP, H.323, FTP ALG',description:'Enable and configure Application-Level Gateways on SRX for NAT traversal.',tags:['juniper','srx','alg','nat','voip','sip'],status:'online',likes:35,dislikes:9,url:'https://www.juniper.net/documentation',scenario_type:'troubleshooting',error_codes:['FLOW-ALG-SIP-INVALID','FLOW-ALG-FTP-DROP']},
  {id:'19',mfr:'f5',title:'BIG-IP iRules — SSL Offload, X-Forwarded-For, Persistence',description:'Write iRules for SSL termination, HTTP header manipulation, URI rewriting.',tags:['f5','big-ip','irules','ssl','http','ltm'],status:'online',likes:66,dislikes:5,url:'https://clouddocs.f5.com/api/irules',scenario_type:'reference',error_codes:['TCL-ERR-01070151','TCL-ERR-01220002']},
  {id:'20',mfr:'f5',title:'BIG-IP DSC Device Trust, Sync Groups, and Connection Mirroring',description:'Configure BIG-IP Device Service Clustering (DSC).',tags:['f5','big-ip','dsc','ha','config-sync'],status:'online',likes:48,dislikes:6,url:'https://techdocs.f5.com/kb/en-us/products/big-ip_ltm',scenario_type:'integration',error_codes:['DSC-01071CB0','DSC-TRUST-0107176F']},
  {id:'21',mfr:'hpe',title:'iLO 5 Factory Reset via Auxiliary Power — Unresponsive BMC Recovery',description:'Recover an unresponsive iLO 5 BMC on ProLiant Gen10/Gen10+.',tags:['hpe','ilo5','bmc','proliant','gen10','reset'],status:'online',likes:92,dislikes:4,url:'https://support.hpe.com/hpesc/public/docDisplay?docId=a00105236en_us',scenario_type:'troubleshooting',error_codes:['ILO-0x0005','ILO-EVT-8217','ILO-BMC-UNRESPONSIVE']},
  {id:'22',mfr:'hpe',title:'iLO 5 HTTPS Certificate Expiration — Renewal and Remote Access Recovery',description:'Restore HTTPS access to iLO 5 after a certificate expires.',tags:['hpe','ilo5','ssl','certificate','ribcl','https'],status:'online',likes:67,dislikes:3,url:'https://support.hpe.com/hpesc/public/docDisplay?docId=c03298644',scenario_type:'troubleshooting',error_codes:['ILO-CERT-0x0038','ERR_CERT_DATE_INVALID','RIBCL-E-0013']},
  {id:'23',mfr:'hpe',title:'HPE OneView Server Profile Compliance Drift — Remediation Workflow',description:'Diagnose Server Profile non-compliance in HPE OneView 5.x/6.x.',tags:['hpe','oneview','server-profile','compliance','synergy'],status:'online',likes:51,dislikes:6,url:'https://techhub.hpe.com/eginfolib/synergy/6.0/s/online-help/',scenario_type:'troubleshooting',error_codes:['OV-PROFILE-NONCOMPLIANT','OV-FW-BASELINE-4017','OV-SAS-4103']},
  {id:'24',mfr:'hpe',title:'HPE MSA 2060 Controller Failover and SAS Cabling Path Validation',description:'Troubleshoot controller failover on MSA 2060/2062 arrays.',tags:['hpe','msa','msa2060','storage','sas','failover'],status:'online',likes:38,dislikes:5,url:'https://support.hpe.com/hpesc/public/docDisplay?docId=sd00002122en_us',scenario_type:'troubleshooting',error_codes:['MSA-A0BC0001','MSA-SAS-LINK-DOWN','MSA-CTLR-FAILOVER-A205']},
  {id:'25',mfr:'hpe',title:'HPE Nimble Storage Group Leader Failover and Volume Resync',description:'Handle Group Leader failover in Nimble Storage arrays.',tags:['hpe','nimble','storage','replication','group-leader'],status:'online',likes:44,dislikes:4,url:'https://infosight.hpe.com/InfoSight/media/cms/active/public/pubs_NimbleOS_6_1_1_Administration_Guide.pdf',scenario_type:'troubleshooting',error_codes:['NIMBLE-EVT-2000','NIMBLE-REPL-LAG-3107','NIMBLE-GL-SPLITBRAIN']},
  {id:'26',mfr:'hpe',title:'HPE Service Pack for ProLiant (SPP) Offline Firmware Flash Procedure',description:'Offline firmware upgrade using HPE SPP on ProLiant Gen10+.',tags:['hpe','spp','firmware','sum','proliant'],status:'broken',likes:29,dislikes:7,url:'https://support.hpe.com/hpesc/public/docDisplay?docId=a00094257en_us',scenario_type:'migration',error_codes:['SPP-SUM-E1078','SPP-BASELINE-MISMATCH','SPP-0x40']},
  {id:'27',mfr:'aruba',title:'ClearPass 802.1X Authentication Failure — Certificate Chain Debug',description:'Root-cause 802.1X failures in ClearPass Policy Manager.',tags:['aruba','clearpass','802.1x','radius','eap-tls'],status:'online',likes:73,dislikes:4,url:'https://www.arubanetworks.com/techdocs/ClearPass/6.11/PolicyManager/',scenario_type:'troubleshooting',error_codes:['CPPM-RADIUS-REJECT','CPPM-EAP-TLS-4013','CPPM-ERR-1201']},
  {id:'28',mfr:'aruba',title:'ClearPass OnGuard Posture Failure — Agent Troubleshooting',description:'Diagnose OnGuard posture check failures.',tags:['aruba','clearpass','onguard','nac','posture'],status:'online',likes:56,dislikes:5,url:'https://www.arubanetworks.com/techdocs/ClearPass/6.11/PolicyManager/',scenario_type:'troubleshooting',error_codes:['ONGUARD-2041','ONGUARD-SHV-MISSING','CPPM-POSTURE-UNHEALTHY']},
  {id:'29',mfr:'aruba',title:'Aruba Instant AP Cluster Firmware Upgrade and Mesh Rollback',description:'Upgrade a mesh Instant AP cluster without outage.',tags:['aruba','instant-ap','mesh','firmware','airwave'],status:'online',likes:42,dislikes:3,url:'https://www.arubanetworks.com/techdocs/Instant_88_X/',scenario_type:'migration',error_codes:['IAP-UPGRADE-305','IAP-MESH-PORTAL-LOST','IAP-VC-FAILOVER']},
  {id:'30',mfr:'aruba',title:'AOS-CX VSX Split-Brain Recovery — ISL Failure Scenarios',description:'Recover from VSX split-brain on AOS-CX 10.x.',tags:['aruba','aos-cx','vsx','split-brain','isl','ha'],status:'online',likes:61,dislikes:6,url:'https://www.arubanetworks.com/techdocs/AOS-CX/10.11/HTML/high_availability/',scenario_type:'troubleshooting',error_codes:['VSX-ISL-DOWN','VSX-SPLIT-BRAIN','VSX-SYNC-ERR-2104']},
  {id:'31',mfr:'aruba',title:'Aruba Central Cloud Onboarding — ZTP and TPM Chain Validation',description:'Onboard CX switches and APs to Aruba Central via ZTP.',tags:['aruba','central','ztp','onboarding','tpm','activate'],status:'online',likes:35,dislikes:4,url:'https://www.arubanetworks.com/techdocs/central/latest/content/nms/',scenario_type:'integration',error_codes:['CENTRAL-ZTP-1301','ACTIVATE-CLAIM-CONFLICT','TPM-ATTEST-FAIL']},
  {id:'32',mfr:'aruba',title:'ClearPass Guest Self-Registration with SMS Sponsor Approval',description:'Configure Guest self-registration with SMS OTP and sponsor approval.',tags:['aruba','clearpass','guest','sms','otp','sponsor'],status:'online',likes:28,dislikes:5,url:'https://www.arubanetworks.com/techdocs/ClearPass/6.11/Guest/',scenario_type:'integration',error_codes:['GUEST-SMS-DELIVERY-FAIL','GUEST-SPONSOR-TIMEOUT','HTTP-429']},
  {id:'33',mfr:'dell',title:'iDRAC9 Lifecycle Controller Firmware Rollback via Web UI',description:'Roll back a failed iDRAC9 / LC firmware update on PowerEdge 14G/15G.',tags:['dell','idrac9','lifecycle-controller','firmware','rollback'],status:'online',likes:84,dislikes:5,url:'https://www.dell.com/support/manuals/en-us/idrac9-lifecycle-controller-v4.x-series/',scenario_type:'troubleshooting',error_codes:['IDRAC-SUP0516','IDRAC-RED128','LC-FW-ROLLBACK-FAIL']},
  {id:'34',mfr:'dell',title:'PowerEdge R750 Backplane PCIe Slot Mapping and Replacement',description:'Replace front backplane on R750 without losing slot mapping.',tags:['dell','poweredge','r750','backplane','perc'],status:'online',likes:57,dislikes:4,url:'https://www.dell.com/support/manuals/en-us/poweredge-r750/per750_ism_pub',scenario_type:'troubleshooting',error_codes:['PDR1016','CPU0000','PERC-FOREIGN-CFG-DETECTED']},
  {id:'35',mfr:'dell',title:'OpenManage Enterprise — SNMPv3 and Redfish Device Discovery',description:'Onboard PowerEdge servers into OME 4.x.',tags:['dell','openmanage','ome','snmp','redfish'],status:'online',likes:46,dislikes:3,url:'https://www.dell.com/support/manuals/en-us/dell-openmanage-enterprise/',scenario_type:'integration',error_codes:['OME-DISC-4091','REDFISH-401','SNMP-V3-AUTH-FAIL']},
  {id:'36',mfr:'dell',title:'Dell PERC H755 Rebuild Priority and Foreign Configuration Import',description:'Manage RAID rebuilds on PERC H755.',tags:['dell','perc','h755','raid','rebuild'],status:'online',likes:52,dislikes:6,url:'https://www.dell.com/support/manuals/en-us/poweredge-rc-h755/perc11_ug',scenario_type:'troubleshooting',error_codes:['PERC-FOREIGN-CFG','PERC-REBUILD-FAILED','PDR64']},
  {id:'37',mfr:'dell',title:'iDRAC9 Virtual Console Certificate Renewal — Java and HTML5 Clients',description:'Renew iDRAC9 web and virtual console certificate.',tags:['dell','idrac9','certificate','virtual-console','racadm'],status:'online',likes:39,dislikes:4,url:'https://infohub.delltechnologies.com/l/security-configuration-guide-integrated-dell-remote-access-controller-9-idrac9-idrac9/',scenario_type:'hardening',error_codes:['IDRAC-SEC0512','RACADM-ERR-CERT-CHAIN','ERR_CERT_COMMON_NAME_INVALID']},
  {id:'38',mfr:'dell',title:'Dell PowerStore T — Volume Creation, Host Mapping, and Async Replication',description:'Provision volumes on PowerStore T.',tags:['dell','powerstore','storage','replication','iscsi','nvme-tcp'],status:'online',likes:33,dislikes:5,url:'https://www.dell.com/support/manuals/en-us/powerstore-1000t/',scenario_type:'integration',error_codes:['PS-REPL-0x2104','PS-HOST-INIT-MISMATCH','PS-RPO-EXCEEDED']},
  {id:'39',mfr:'splunk',title:'Splunk OTEL Collector for VMware vSphere — Metrics Pipeline Setup',description:'Deploy the Splunk Distribution of OpenTelemetry Collector to scrape vCenter metrics via the vmware receiver.',tags:['splunk','otel','vmware','vcenter','observability','metrics'],status:'online',likes:44,dislikes:2,url:'https://docs.splunk.com/observability/en/gdi/opentelemetry/components/vmware-receiver.html',scenario_type:'integration',error_codes:['SPL-OTEL-1001','OTEL-VMW-AUTH-FAIL','GOVMOMI-INVALID-LOGIN']},
  {id:'40',mfr:'splunk',title:'OTEL Collector on Bare-Metal Linux — systemd, hostmetrics, cgroup v2',description:'Install otelcol-contrib on RHEL 9 / Ubuntu 22.04 bare-metal.',tags:['splunk','otel','linux','bare-metal','systemd','hostmetrics'],status:'online',likes:38,dislikes:3,url:'https://docs.splunk.com/observability/en/gdi/opentelemetry/install-linux.html',scenario_type:'hardening',error_codes:['SPL-OTEL-2014','OTEL-EXPORTER-TIMEOUT','SYSTEMD-203']},
  {id:'41',mfr:'splunk',title:'Universal Forwarder Tuning on Citrix VDAs — I/O and CPU Ceiling',description:'Tame Universal Forwarder on Citrix VDAs.',tags:['splunk','universal-forwarder','citrix','vda','pvs','tuning'],status:'online',likes:52,dislikes:4,url:'https://docs.splunk.com/Documentation/Forwarder/latest/Forwarder/Configureaggregatorprocessor',scenario_type:'hardening',error_codes:['SPL-UF-3008','UF-THRUPUT-BLOCKED','UF-PARSING-QUEUE-FULL']},
  {id:'42',mfr:'splunk',title:'HEC Indexer Discovery and Load Balancing for OTEL Exporters',description:'Replace static HEC endpoints with indexer discovery.',tags:['splunk','hec','otel','indexer-discovery','load-balancing'],status:'online',likes:41,dislikes:3,url:'https://docs.splunk.com/observability/en/gdi/opentelemetry/components/splunk-hec-exporter.html',scenario_type:'integration',error_codes:['SPL-HEC-4010','HEC-ACK-TIMEOUT','HTTP-503']},
  {id:'43',mfr:'splunk',title:'Splunk ITSI Glass Tables from OTEL Signals — KPI Wiring',description:'Wire OTEL metrics into ITSI service trees.',tags:['splunk','itsi','otel','kpi','glass-tables'],status:'online',likes:29,dislikes:4,url:'https://docs.splunk.com/Documentation/ITSI/latest/User/AboutITSI',scenario_type:'integration',error_codes:['SPL-ITSI-5021','ITSI-KPI-NO-DATA','ITSI-ENTITY-IMPORT-FAIL']},
  {id:'44',mfr:'citrix',title:'Citrix Cloud API — Bearer Token Rotation and Rate Limit Handling',description:'Authenticate against Citrix Cloud REST API.',tags:['citrix','citrix-cloud','api','oauth','rate-limit'],status:'online',likes:47,dislikes:3,url:'https://developer.cloud.com/citrix-cloud/citrix-cloud-api-overview/docs/get-started-with-citrix-cloud-apis',scenario_type:'integration',error_codes:['CTX-API-401','CTX-API-429','CTX-TOKEN-EXPIRED','HTTP-401','HTTP-429']},
  {id:'45',mfr:'citrix',title:'Citrix Monitor OData API — Session Telemetry for Splunk Ingest',description:'Pull session, connection failure, ICA RTT metrics via Monitor OData v4.',tags:['citrix','monitor','odata','telemetry','splunk','cim'],status:'online',likes:36,dislikes:4,url:'https://developer-docs.citrix.com/projects/monitor-service-odata-api/en/latest/',scenario_type:'integration',error_codes:['CTX-ODATA-400','CTX-ODATA-DELTATOKEN-EXPIRED','CTX-MON-SESSION-LOST','HTTP-429']},
  {id:'46',mfr:'citrix',title:'NSX-T Edge Node Metrics via Splunk OTEL — prometheusreceiver Wiring',description:'Scrape NSX-T Edge Node /stats endpoints using OTEL prometheusreceiver.',tags:['citrix','nsx-t','edge','prometheus','otel','metrics'],status:'online',likes:31,dislikes:5,url:'https://docs.vmware.com/en/VMware-NSX/4.1/administration/',scenario_type:'integration',error_codes:['NSX-EDGE-STATS-503','OTEL-PROM-SCRAPE-FAIL','NSX-PI-CERT-INVALID','HTTP-503']},
  {id:'47',mfr:'citrix',title:'Citrix ADC (NetScaler) AppFlow to Splunk — HDX Insight Export',description:'Enable AppFlow on Citrix ADC for HDX Insight.',tags:['citrix','adc','netscaler','appflow','hdx-insight','ipfix'],status:'online',likes:42,dislikes:3,url:'https://docs.netscaler.com/en-us/citrix-adc/current-release/ns-ag-appflow-intro-wrapper-con.html',scenario_type:'integration',error_codes:['NS-APPFLOW-TEMPLATE-FAIL','NS-IPFIX-COLLECTOR-DOWN','NS-CPU-HIGH-4403']},
  {id:'48',mfr:'citrix',title:'FSLogix Profile Container Corruption — VHDX Repair on Citrix VDAs',description:'Diagnose and recover corrupted FSLogix profile containers.',tags:['citrix','fslogix','vhdx','profile','vda'],status:'online',likes:88,dislikes:6,url:'https://learn.microsoft.com/en-us/fslogix/troubleshooting-events-errors',scenario_type:'troubleshooting',error_codes:['FSLOGIX-26','FSLOGIX-52','FRXSVC-31009','0x0000003B']},
].map(a=>({...a,mfrName:VN[a.mfr],mfrColor:VC[a.mfr]}));

const ACADEMY=[
  {id:'a1',cert:'VCP',certColor:'#1d6fa5',level:'associate',title:'VCP-DCV 2024 — vSphere 8 Official Exam Prep',description:'VMware official study guide.',tags:['vsphere','vcenter','esxi'],free:true,url:'https://www.vmware.com/learning/certification'},
  {id:'a2',cert:'VCP',certColor:'#1d6fa5',level:'professional',title:'VCAP-DCV Design 3V0-624',description:'Advanced design exam.',tags:['design','architecture'],free:false,url:'https://www.vmware.com/learning'},
  {id:'a3',cert:'CCNA',certColor:'#049fd9',level:'beginner',title:'Cisco Networking Basics — NetAcad',description:'Entry-level networking.',tags:['fundamentals','osi','ip'],free:true,url:'https://www.netacad.com'},
  {id:'a4',cert:'CCNA',certColor:'#049fd9',level:'associate',title:'Cisco CCNA 200-301 — Full Study Guide',description:'Comprehensive CCNA prep.',tags:['routing','switching','ospf'],free:true,url:'https://www.netacad.com'},
  {id:'a5',cert:'CCNP',certColor:'#049fd9',level:'professional',title:'CCNP Enterprise ENCOR 350-401',description:'Enterprise infrastructure.',tags:['sd-wan','bgp','qos'],free:false,url:'https://www.cisco.com/c/en/us/training-events/training-certifications'},
  {id:'a6',cert:'CCIE',certColor:'#049fd9',level:'expert',title:'CCIE Enterprise Infrastructure v1.1 Lab Prep',description:'Advanced lab preparation.',tags:['mpls','segment-routing','evpn'],free:false,url:'https://www.cisco.com/c/en/us/training-events/training-certifications'},
  {id:'a7',cert:'CISSP',certColor:'#8b5cf6',level:'professional',title:'CISSP Official Study Guide 9th Edition',description:'ISC2 official material.',tags:['security','iam','cryptography'],free:false,url:'https://www.isc2.org/certifications/cissp'},
  {id:'a8',cert:'CEH',certColor:'#ef4444',level:'professional',title:'CEH v12 — Certified Ethical Hacker',description:'EC-Council courseware.',tags:['pentest','vulnerability','kali'],free:false,url:'https://www.eccouncil.org/train-certify/certified-ethical-hacker-ceh'},
  {id:'a9',cert:'PCNSA',certColor:'#fa582d',level:'associate',title:'Palo Alto PCNSA Study Guide',description:'PCNSA exam preparation.',tags:['palo-alto','ngfw','pan-os'],free:true,url:'https://www.paloaltonetworks.com/services/education'},
  {id:'a10',cert:'NSE4',certColor:'#ee3124',level:'associate',title:'Fortinet NSE 4 — FortiGate Security',description:'NSE4 certification prep.',tags:['fortinet','fortigate','vpn'],free:true,url:'https://training.fortinet.com'},
];

const MANUFACTURERS=Object.keys(VN).map(id=>({id,name:VN[id]}));
const CERT_LEVELS=['beginner','associate','professional','expert'];
const CERTS=['VCP','CCNA','CCNP','CCIE','CISSP','CEH','PCNSA','NSE4'];

// ══════════════════════════════════════════════════════════════
//  Client-side mirror of GET /api/kb/error-codes/stats
//  Runs the same aggregation logic the SQL CTE does.
//  Wrapped in useMemo so re-filtering doesn't recompute.
// ══════════════════════════════════════════════════════════════
function computeErrorCodeStats(articles, limit=10){
  const codeMap=new Map(); // code → { frequency, vendors:Set, sample_id }
  let articlesWithCodes=0;
  for(const a of articles){
    if(!a.error_codes||!a.error_codes.length)continue;
    articlesWithCodes++;
    for(const raw of a.error_codes){
      const code=raw.trim().toUpperCase();
      if(!code)continue;
      let entry=codeMap.get(code);
      if(!entry){entry={frequency:0,vendors:new Set(),sample_article_id:a.id};codeMap.set(code,entry);}
      entry.frequency++;
      entry.vendors.add(a.mfr);
    }
  }
  const all=[...codeMap.entries()].map(([code,v])=>({code,frequency:v.frequency,vendors:[...v.vendors].sort(),sample_article_id:v.sample_article_id}));
  all.sort((a,b)=>b.frequency-a.frequency||a.code.localeCompare(b.code));
  return{
    total_unique_codes:codeMap.size,
    total_code_uses:all.reduce((s,x)=>s+x.frequency,0),
    articles_with_codes:articlesWithCodes,
    top:all.slice(0,limit),
  };
}

function ngrams(s,n){const g=[];for(let i=0;i<=s.length-n;i++)g.push(s.slice(i,i+n));return g;}
function trigramSim(text,q){if(q.length<3)return text.includes(q)?0.6:0;const tg=new Set(ngrams(text,3)),qg=ngrams(q,3);return qg.length?qg.filter(g=>tg.has(g)).length/qg.length:0;}
function scoreArt(a,query){
  if(!query.trim())return 1;
  const q=query.toLowerCase().trim(),title=a.title.toLowerCase(),desc=a.description.toLowerCase(),tags=a.tags.join(' ').toLowerCase(),mfr=a.mfrName.toLowerCase();
  const codes=(a.error_codes||[]).join(' ').toLowerCase();
  if(title.includes(q))return 1.0;
  if(codes.includes(q))return 0.97;
  if(mfr.includes(q))return 0.95;if(desc.includes(q)||tags.includes(q))return 0.85;
  const words=q.split(/\s+/).filter(w=>w.length>2);if(!words.length)return trigramSim(title,q)*0.7;
  let best=0;for(const w of words){if(title.includes(w))best=Math.max(best,0.88);else if(desc.includes(w)||tags.includes(w)||codes.includes(w))best=Math.max(best,0.72);else best=Math.max(best,trigramSim(title,w)*0.7,trigramSim(desc,w)*0.45);}
  return best;
}
function calcScore(a,votes){const v=votes[a.id],likes=a.likes+(v==='like'?1:0),dislikes=a.dislikes+(v==='dislike'?1:0),total=likes+dislikes;return{likes,dislikes,total,pct:total?Math.round(100*likes/total):null};}

function StatusPill({status,t}){
  const cfg={online:{color:C.green,bg:'#1a3128',icon:<Wifi size={10}/>,label:t.online},broken:{color:C.red,bg:'#3d1a1a',icon:<WifiOff size={10}/>,label:t.broken},unchecked:{color:C.t2,bg:C.hover,icon:<AlertCircle size={10}/>,label:t.unchecked}}[status]||{color:C.t2,bg:C.hover,icon:null,label:status};
  return(<span style={{display:'inline-flex',alignItems:'center',gap:4,background:cfg.bg,color:cfg.color,fontSize:10,fontFamily:mono,padding:'2px 7px',borderRadius:99,border:`1px solid ${cfg.color}33`}}>{cfg.icon}{cfg.label}</span>);
}
function ScenarioPill({scenario}){if(!scenario)return null;const color={troubleshooting:C.red,integration:C.blue,hardening:C.amber,migration:C.purple,reference:C.t1}[scenario]||C.t2;return(<span style={{fontSize:10,fontFamily:mono,color,background:color+'15',border:`1px solid ${color}44`,borderRadius:99,padding:'1px 7px',textTransform:'capitalize'}}>{scenario}</span>);}
function Tag({tag}){return(<span style={{fontSize:10,fontFamily:mono,color:C.t1,background:C.surface2,border:`1px solid ${C.border}`,borderRadius:4,padding:'1px 6px'}}>{tag}</span>);}
function ErrorCode({code,small}){return(<span style={{fontSize:small?10:11,fontFamily:mono,color:C.amber,background:C.amber+(small?'15':'22'),border:`1px solid ${C.amber}${small?'44':'55'}`,borderRadius:4,padding:small?'1px 6px':'2px 7px',fontWeight:600}}>{code}</span>);}
function MfrBadge({name,color}){return(<span style={{fontSize:10,fontWeight:600,fontFamily:mono,color,background:color+'22',border:`1px solid ${color}44`,borderRadius:4,padding:'1px 7px'}}>{name}</span>);}
function ResBar({pct}){if(pct===null)return null;const color=pct>=80?C.green:pct>=55?C.amber:C.red;return(<div style={{display:'flex',alignItems:'center',gap:6}}><div style={{flex:1,height:3,background:C.border,borderRadius:99}}><div style={{width:`${pct}%`,height:'100%',background:color,borderRadius:99}}/></div><span style={{fontSize:11,fontFamily:mono,color,minWidth:34,textAlign:'right'}}>{pct}%</span></div>);}

// ══════════════════════════════════════════════════════════════
//  Top Error Codes widget — clickable rows that filter the grid
// ══════════════════════════════════════════════════════════════
function TopErrorCodes({stats,activeCode,onPick,t}){
  const maxFreq=Math.max(...stats.top.map(x=>x.frequency),1);
  return(
    <div style={{background:C.surface,border:`1px solid ${C.border}`,borderRadius:8,marginBottom:20,overflow:'hidden'}}>
      <div style={{display:'flex',alignItems:'center',gap:10,padding:'12px 16px',borderBottom:`1px solid ${C.border}`,background:`linear-gradient(90deg,${C.amber}0d,transparent)`}}>
        <TrendingUp size={15} color={C.amber}/>
        <div style={{flex:1}}>
          <div style={{display:'flex',alignItems:'baseline',gap:8}}>
            <span style={{fontSize:13,fontWeight:700,color:C.t0}}>{t.topCodes}</span>
            <span style={{fontSize:10,fontFamily:mono,color:C.t2}}>GET /api/kb/error-codes/stats</span>
          </div>
          <div style={{fontSize:11,color:C.t2,marginTop:2}}>{t.topCodesDesc} · {t.clickToFilter}</div>
        </div>
        <div style={{display:'flex',gap:14,fontFamily:mono,fontSize:11}}>
          <span><span style={{color:C.amber,fontWeight:600}}>{stats.total_unique_codes}</span> <span style={{color:C.t2}}>{t.uniqueCodes}</span></span>
          <span><span style={{color:C.amber,fontWeight:600}}>{stats.total_code_uses}</span> <span style={{color:C.t2}}>{t.totalUses}</span></span>
          <span><span style={{color:C.amber,fontWeight:600}}>{stats.articles_with_codes}</span> <span style={{color:C.t2}}>{t.withCodes}</span></span>
        </div>
      </div>
      <div style={{padding:'8px'}}>
        {stats.top.map((row,idx)=>{
          const isActive=activeCode===row.code;
          const barPct=(row.frequency/maxFreq)*100;
          return(
            <button key={row.code} onClick={()=>onPick(isActive?'':row.code)}
              style={{display:'flex',alignItems:'center',gap:10,width:'100%',padding:'8px 10px',background:isActive?C.amber+'22':'transparent',border:`1px solid ${isActive?C.amber+'66':'transparent'}`,borderRadius:6,cursor:'pointer',textAlign:'left',fontFamily:sans,transition:'background .12s'}}
              onMouseEnter={e=>{if(!isActive)e.currentTarget.style.background=C.hover;}}
              onMouseLeave={e=>{if(!isActive)e.currentTarget.style.background='transparent';}}>
              <span style={{fontSize:11,fontFamily:mono,color:C.t2,minWidth:22,textAlign:'right',fontWeight:600}}>#{idx+1}</span>
              <span style={{minWidth:180,display:'flex'}}><ErrorCode code={row.code}/></span>
              <div style={{flex:1,minWidth:120,display:'flex',alignItems:'center',gap:8}}>
                <div style={{flex:1,height:4,background:C.border,borderRadius:99,overflow:'hidden'}}>
                  <div style={{width:`${barPct}%`,height:'100%',background:isActive?C.amber:C.amber+'88',transition:'width .3s'}}/>
                </div>
                <span style={{fontSize:11,fontFamily:mono,color:isActive?C.amber:C.t1,fontWeight:600,minWidth:28,textAlign:'right'}}>×{row.frequency}</span>
              </div>
              <div style={{display:'flex',gap:3,flexWrap:'wrap',minWidth:140,justifyContent:'flex-end'}}>
                {row.vendors.slice(0,4).map(v=>(
                  <span key={v} title={VN[v]} style={{fontSize:9,fontFamily:mono,fontWeight:700,color:VC[v]||C.t1,background:(VC[v]||C.t1)+'22',border:`1px solid ${(VC[v]||C.t1)}44`,borderRadius:3,padding:'1px 5px'}}>{v}</span>
                ))}
                {row.vendors.length>4&&<span style={{fontSize:9,fontFamily:mono,color:C.t2}}>+{row.vendors.length-4}</span>}
              </div>
            </button>
          );
        })}
      </div>
      {activeCode&&(
        <div style={{padding:'8px 14px',background:C.amber+'15',borderTop:`1px solid ${C.amber}33`,display:'flex',alignItems:'center',gap:8}}>
          <Bug size={11} color={C.amber}/>
          <span style={{fontSize:11,color:C.amber,fontFamily:mono}}>{t.filtering}: <strong>{activeCode}</strong></span>
          <span style={{flex:1}}/>
          <button onClick={()=>onPick('')} style={{display:'flex',alignItems:'center',gap:4,background:'none',border:`1px solid ${C.amber}55`,color:C.amber,fontSize:10,fontFamily:mono,padding:'3px 8px',borderRadius:4,cursor:'pointer'}}>
            <X size={10}/>{t.filterCleared}
          </button>
        </div>
      )}
    </div>
  );
}

function KBCard({article:a,t,votes,onVote,onSelect,selected,highlightCode}){
  const{likes,dislikes,total,pct}=calcScore(a,votes),myVote=votes[a.id],isSelected=selected===a.id;
  return(
    <div onClick={()=>onSelect(isSelected?null:a.id)} style={{background:isSelected?C.surface2:C.surface,border:`1px solid ${isSelected?C.blue+'66':C.border}`,borderRadius:8,padding:'14px 16px',cursor:'pointer',transition:'border-color .15s'}}>
      <div style={{display:'flex',alignItems:'flex-start',justifyContent:'space-between',gap:8,marginBottom:8}}>
        <div style={{display:'flex',gap:6,flexWrap:'wrap',alignItems:'center'}}>
          <MfrBadge name={a.mfrName} color={a.mfrColor}/>
          <StatusPill status={a.status} t={t}/>
          <ScenarioPill scenario={a.scenario_type}/>
        </div>
        <ChevronRight size={14} color={C.t2} style={{transform:isSelected?'rotate(90deg)':'none',transition:'transform .2s',flexShrink:0}}/>
      </div>
      <h3 style={{fontSize:13,fontWeight:600,color:C.t0,lineHeight:1.4,marginBottom:6}}>{a.title}</h3>
      <p style={{fontSize:12,color:C.t1,lineHeight:1.55,marginBottom:10,display:'-webkit-box',WebkitLineClamp:2,WebkitBoxOrient:'vertical',overflow:'hidden'}}>{a.description}</p>
      <div style={{display:'flex',flexWrap:'wrap',gap:4,marginBottom:10}}>{a.tags.slice(0,5).map(tag=><Tag key={tag} tag={tag}/>)}</div>
      {a.error_codes&&a.error_codes.length>0&&(
        <div style={{display:'flex',flexWrap:'wrap',gap:4,marginBottom:10,alignItems:'center'}}>
          <Bug size={10} color={C.amber}/>
          {a.error_codes.slice(0,3).map(code=>{
            const hl=highlightCode&&code.toUpperCase()===highlightCode.toUpperCase();
            return<span key={code} style={{fontSize:10,fontFamily:mono,color:hl?'#000':C.amber,background:hl?C.amber:C.amber+'15',border:`1px solid ${C.amber}${hl?'':'44'}`,borderRadius:4,padding:'1px 6px',fontWeight:600}}>{code}</span>;
          })}
          {a.error_codes.length>3&&<span style={{fontSize:10,fontFamily:mono,color:C.t2}}>+{a.error_codes.length-3}</span>}
        </div>
      )}
      {pct!==null&&<ResBar pct={pct}/>}
      {isSelected&&(
        <div style={{marginTop:14,paddingTop:14,borderTop:`1px solid ${C.border}`}} onClick={e=>e.stopPropagation()}>
          <p style={{fontSize:12,color:C.t1,lineHeight:1.65,marginBottom:12}}>{a.description}</p>
          <div style={{display:'flex',flexWrap:'wrap',gap:4,marginBottom:14}}>{a.tags.map(tag=><Tag key={tag} tag={tag}/>)}</div>
          {a.error_codes&&a.error_codes.length>0&&(
            <div style={{marginBottom:12,padding:'8px 10px',background:C.amber+'0d',border:`1px solid ${C.amber}33`,borderRadius:6}}>
              <div style={{fontSize:10,color:C.amber,fontFamily:mono,fontWeight:600,marginBottom:6,display:'flex',alignItems:'center',gap:5}}>
                <Bug size={11}/>{t.errorCodes} ({a.error_codes.length})
              </div>
              <div style={{display:'flex',flexWrap:'wrap',gap:4}}>
                {a.error_codes.map(code=><ErrorCode key={code} code={code}/>)}
              </div>
            </div>
          )}
          <div style={{display:'flex',alignItems:'center',gap:8,flexWrap:'wrap'}}>
            <a href={a.url} target="_blank" rel="noopener noreferrer" style={{display:'inline-flex',alignItems:'center',gap:6,background:C.blueD,color:'#fff',fontSize:12,padding:'6px 14px',borderRadius:6,textDecoration:'none',fontWeight:500}}>
              <ExternalLink size={12}/>{t.viewDocs}
            </a>
            <span style={{flex:1}}/>
            <span style={{fontSize:11,color:C.t2,fontFamily:mono}}>{t.loginVote}</span>
            <button onClick={()=>onVote(a.id,'like')} style={{display:'flex',alignItems:'center',gap:5,fontSize:12,padding:'5px 12px',borderRadius:6,border:`1px solid ${myVote==='like'?C.green:C.border}`,background:myVote==='like'?C.teal+'22':C.hover,color:myVote==='like'?C.green:C.t1,cursor:'pointer',fontFamily:sans}}>
              <ThumbsUp size={12}/>{likes}
            </button>
            <button onClick={()=>onVote(a.id,'dislike')} style={{display:'flex',alignItems:'center',gap:5,fontSize:12,padding:'5px 12px',borderRadius:6,border:`1px solid ${myVote==='dislike'?C.red:C.border}`,background:myVote==='dislike'?C.red+'22':C.hover,color:myVote==='dislike'?C.red:C.t1,cursor:'pointer',fontFamily:sans}}>
              <ThumbsDown size={12}/>{dislikes}
            </button>
          </div>
          {total>0&&<p style={{marginTop:8,fontSize:11,color:C.t2,fontFamily:mono}}>{t.resolution}: {pct}% · {total} {t.votes}</p>}
        </div>
      )}
    </div>
  );
}

function AcademyCard({r,t}){
  const levelColor={beginner:C.green,associate:C.blue,professional:C.purple,expert:C.amber}[r.level]||C.t1;
  return(
    <a href={r.url} target="_blank" rel="noopener noreferrer" style={{textDecoration:'none',display:'block',background:C.surface,border:`1px solid ${C.border}`,borderRadius:8,padding:'14px 16px'}}>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:8,gap:8}}>
        <div style={{display:'flex',gap:6,flexWrap:'wrap'}}>
          <span style={{fontSize:11,fontWeight:700,fontFamily:mono,color:r.certColor,background:r.certColor+'22',border:`1px solid ${r.certColor}44`,borderRadius:4,padding:'1px 7px'}}>{r.cert}</span>
          <span style={{fontSize:10,fontFamily:mono,color:levelColor,background:levelColor+'1a',border:`1px solid ${levelColor}44`,borderRadius:99,padding:'1px 8px',textTransform:'capitalize'}}>{t[r.level]}</span>
        </div>
        <div style={{display:'flex',alignItems:'center',gap:4,flexShrink:0}}>
          {r.free?<span style={{fontSize:10,color:C.green,fontFamily:mono,background:'#1a3128',border:`1px solid ${C.green}33`,borderRadius:99,padding:'1px 7px'}}>{t.free}</span>:<span style={{fontSize:10,color:C.t2,fontFamily:mono}}>{t.paid}</span>}
          <ExternalLink size={12} color={C.t2}/>
        </div>
      </div>
      <h3 style={{fontSize:13,fontWeight:600,color:C.t0,lineHeight:1.4,marginBottom:5}}>{r.title}</h3>
      <p style={{fontSize:12,color:C.t1,lineHeight:1.5,marginBottom:8,display:'-webkit-box',WebkitLineClamp:2,WebkitBoxOrient:'vertical',overflow:'hidden'}}>{r.description}</p>
      <div style={{display:'flex',flexWrap:'wrap',gap:4}}>{r.tags.map(tag=><Tag key={tag} tag={tag}/>)}</div>
    </a>
  );
}

export default function App(){
  const[page,setPage]=useState('kb');
  const[lang,setLang]=useState('es');
  const[query,setQuery]=useState('');
  const[mfr,setMfr]=useState('all');
  const[statusF,setStatusF]=useState('all');
  const[onlyErrors,setOnlyErrors]=useState(false);
  const[errorCodeQuery,setErrorCodeQuery]=useState('');
  const[votes,setVotes]=useState({});
  const[selected,setSelected]=useState(null);
  const[certF,setCertF]=useState('all');
  const[levelF,setLevelF]=useState('all');
  const[freeOnly,setFreeOnly]=useState(false);
  const t=T[lang];

  const errorStats=useMemo(()=>computeErrorCodeStats(ARTICLES,10),[]);

  const filteredArticles=useMemo(()=>{
    const ecq=errorCodeQuery.trim().toUpperCase();
    return ARTICLES.map(a=>({...a,_score:scoreArt(a,query)}))
      .filter(a=>
        a._score>0.12
        &&(mfr==='all'||a.mfr===mfr)
        &&(statusF==='all'||a.status===statusF)
        &&(!onlyErrors||(a.error_codes&&a.error_codes.length>0))
        &&(!ecq||(a.error_codes||[]).some(c=>c.toUpperCase()===ecq))
      )
      .sort((a,b)=>b._score-a._score);
  },[query,mfr,statusF,onlyErrors,errorCodeQuery]);

  const filteredAcademy=useMemo(()=>
    ACADEMY.filter(r=>(certF==='all'||r.cert===certF)&&(levelF==='all'||r.level===levelF)&&(!freeOnly||r.free)),
  [certF,levelF,freeOnly]);

  function handleVote(id,vote){setVotes(prev=>{if(prev[id]===vote){const n={...prev};delete n[id];return n;}return{...prev,[id]:vote};});}
  function handlePickCode(code){setErrorCodeQuery(code);setSelected(null);if(code)window.scrollTo({top:0,behavior:'smooth'});}

  const mfrCounts=useMemo(()=>{const c={};ARTICLES.forEach(a=>{c[a.mfr]=(c[a.mfr]||0)+1;});return c;},[]);
  const totalErrorCodes=useMemo(()=>ARTICLES.reduce((s,a)=>s+(a.error_codes||[]).length,0),[]);

  const navBtn=(id,icon,label)=>(
    <button key={id} onClick={()=>setPage(id)} style={{display:'flex',alignItems:'center',gap:7,padding:'7px 14px',borderRadius:6,border:'none',cursor:'pointer',fontSize:13,fontWeight:500,background:page===id?C.surface2:'transparent',color:page===id?C.t0:C.t1}}>{icon}{label}</button>
  );

  return(
    <div style={{background:C.bg,color:C.t0,fontFamily:sans,minHeight:700}}>
      <header style={{background:C.surface,borderBottom:`1px solid ${C.border}`,position:'sticky',top:0,zIndex:50}}>
        <div style={{maxWidth:1100,margin:'0 auto',padding:'0 20px',display:'flex',alignItems:'center',gap:16,height:52}}>
          <div style={{display:'flex',alignItems:'center',gap:9}}>
            <div style={{width:28,height:28,borderRadius:6,background:C.blueD,display:'flex',alignItems:'center',justifyContent:'center'}}><Database size={15} color="#fff"/></div>
            <span style={{fontWeight:700,fontSize:15,color:C.t0,fontFamily:mono,letterSpacing:'-0.5px'}}>TechKB</span>
          </div>
          <nav style={{display:'flex',gap:2,flex:1}}>{navBtn('kb',<Layers size={14}/>,t.kb)}{navBtn('academy',<Award size={14}/>,t.academy)}</nav>
          <div style={{display:'flex',background:C.surface2,border:`1px solid ${C.border}`,borderRadius:6,overflow:'hidden'}}>
            {['en','es'].map(l=>(<button key={l} onClick={()=>setLang(l)} style={{padding:'4px 12px',fontSize:11,fontFamily:mono,fontWeight:600,border:'none',cursor:'pointer',background:lang===l?C.blueD:'transparent',color:lang===l?'#fff':C.t1}}>{l.toUpperCase()}</button>))}
          </div>
        </div>
      </header>

      <div style={{maxWidth:1100,margin:'0 auto',padding:'24px 20px'}}>
        {page==='kb'&&(
          <>
            <div style={{marginBottom:20}}>
              <h1 style={{fontSize:22,fontWeight:700,color:C.t0,marginBottom:4}}>{t.kb}</h1>
              <p style={{fontSize:13,color:C.t1}}>{t.tagline} · {ARTICLES.length} {t.articles} · 12 vendors · <span style={{color:C.amber,fontFamily:mono}}>{totalErrorCodes} error codes</span></p>
            </div>

            <TopErrorCodes stats={errorStats} activeCode={errorCodeQuery} onPick={handlePickCode} t={t}/>

            <div style={{position:'relative',marginBottom:12}}>
              <Search size={15} color={C.t2} style={{position:'absolute',left:13,top:'50%',transform:'translateY(-50%)',pointerEvents:'none'}}/>
              <input value={query} onChange={e=>{setQuery(e.target.value);setSelected(null);}} placeholder={t.search} type="search"
                style={{width:'100%',boxSizing:'border-box',padding:'10px 14px 10px 38px',background:C.surface,border:`1px solid ${C.border}`,borderRadius:8,color:C.t0,fontSize:14,fontFamily:sans,outline:'none'}}
                onFocus={e=>e.target.style.borderColor=`${C.blue}88`} onBlur={e=>e.target.style.borderColor=C.border}/>
              {query&&<button onClick={()=>setQuery('')} style={{position:'absolute',right:10,top:'50%',transform:'translateY(-50%)',background:'none',border:'none',cursor:'pointer',color:C.t2,display:'flex'}}><X size={14}/></button>}
            </div>
            <div style={{display:'flex',gap:8,flexWrap:'wrap',marginBottom:20,alignItems:'center'}}>
              <select value={mfr} onChange={e=>{setMfr(e.target.value);setSelected(null);}} style={{padding:'6px 10px',background:C.surface,border:`1px solid ${C.border}`,borderRadius:6,color:C.t0,fontSize:12,fontFamily:mono,cursor:'pointer'}}>
                <option value="all">{t.allVendors}</option>
                {MANUFACTURERS.map(m=><option key={m.id} value={m.id}>{m.name} ({mfrCounts[m.id]||0})</option>)}
              </select>
              <select value={statusF} onChange={e=>{setStatusF(e.target.value);setSelected(null);}} style={{padding:'6px 10px',background:C.surface,border:`1px solid ${C.border}`,borderRadius:6,color:C.t0,fontSize:12,fontFamily:mono,cursor:'pointer'}}>
                <option value="all">{t.allStatuses}</option>
                <option value="online">{t.online}</option>
                <option value="broken">{t.broken}</option>
              </select>
              <label style={{display:'flex',alignItems:'center',gap:6,fontSize:12,color:onlyErrors?C.amber:C.t1,cursor:'pointer',padding:'6px 10px',background:onlyErrors?C.amber+'22':C.surface,border:`1px solid ${onlyErrors?C.amber+'88':C.border}`,borderRadius:6,fontFamily:mono,fontWeight:onlyErrors?600:400}}>
                <input type="checkbox" checked={onlyErrors} onChange={e=>{setOnlyErrors(e.target.checked);setSelected(null);}} style={{accentColor:C.amber}}/>
                <Bug size={12} color={onlyErrors?C.amber:C.t2}/>
                {t.onlyErrors}
              </label>
              <input value={errorCodeQuery} onChange={e=>{setErrorCodeQuery(e.target.value);setSelected(null);}} placeholder={t.errorCodePlaceholder}
                style={{padding:'6px 10px',background:C.surface,border:`1px solid ${errorCodeQuery?C.amber+'88':C.border}`,borderRadius:6,color:errorCodeQuery?C.amber:C.t0,fontSize:12,fontFamily:mono,width:210,outline:'none'}}
                onFocus={e=>e.target.style.borderColor=`${C.amber}88`} onBlur={e=>e.target.style.borderColor=errorCodeQuery?C.amber+'88':C.border}/>
              <span style={{fontSize:12,color:C.t2,fontFamily:mono}}>{filteredArticles.length}/{ARTICLES.length} {t.articles}</span>
              <div style={{marginLeft:'auto',display:'flex',gap:12}}>
                <span style={{fontSize:11,fontFamily:mono,color:C.green}}>{ARTICLES.filter(a=>a.status==='online').length} {t.online}</span>
                <span style={{fontSize:11,fontFamily:mono,color:C.red}}>{ARTICLES.filter(a=>a.status==='broken').length} {t.broken}</span>
              </div>
            </div>
            {filteredArticles.length===0?(
              <div style={{textAlign:'center',padding:'60px 0',color:C.t2}}><Search size={32} color={C.border} style={{margin:'0 auto 12px'}}/><p style={{fontSize:14}}>{t.noResults}</p></div>
            ):(
              <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(340px,1fr))',gap:12}}>
                {filteredArticles.map(a=><KBCard key={a.id} article={a} t={t} votes={votes} onVote={handleVote} onSelect={setSelected} selected={selected} highlightCode={errorCodeQuery}/>)}
              </div>
            )}
          </>
        )}

        {page==='academy'&&(
          <>
            <div style={{marginBottom:20}}><h1 style={{fontSize:22,fontWeight:700,color:C.t0,marginBottom:4}}>{t.certResources}</h1><p style={{fontSize:13,color:C.t1}}>{t.academy} · {ACADEMY.length} {t.articles}</p></div>
            <div style={{display:'flex',gap:8,flexWrap:'wrap',marginBottom:24,alignItems:'center'}}>
              <select value={certF} onChange={e=>setCertF(e.target.value)} style={{padding:'6px 10px',background:C.surface,border:`1px solid ${C.border}`,borderRadius:6,color:C.t0,fontSize:12,fontFamily:mono,cursor:'pointer'}}>
                <option value="all">{t.allCerts}</option>{CERTS.map(c=><option key={c} value={c}>{c}</option>)}
              </select>
              <select value={levelF} onChange={e=>setLevelF(e.target.value)} style={{padding:'6px 10px',background:C.surface,border:`1px solid ${C.border}`,borderRadius:6,color:C.t0,fontSize:12,fontFamily:mono,cursor:'pointer'}}>
                <option value="all">{t.allLevels}</option>{CERT_LEVELS.map(l=><option key={l} value={l}>{t[l]}</option>)}
              </select>
              <label style={{display:'flex',alignItems:'center',gap:6,fontSize:12,color:C.t1,cursor:'pointer'}}><input type="checkbox" checked={freeOnly} onChange={e=>setFreeOnly(e.target.checked)} style={{accentColor:C.green}}/>{t.free} only</label>
              <span style={{fontSize:12,color:C.t2,fontFamily:mono,marginLeft:4}}>{filteredAcademy.length} {t.articles}</span>
            </div>
            {(()=>{
              const groups={};filteredAcademy.forEach(r=>{if(!groups[r.cert])groups[r.cert]=[];groups[r.cert].push(r);});
              if(!Object.keys(groups).length)return<p style={{color:C.t2,textAlign:'center',padding:'60px 0'}}>{t.noResults}</p>;
              return Object.entries(groups).map(([cert,items])=>(
                <div key={cert} style={{marginBottom:32}}>
                  <div style={{display:'flex',alignItems:'center',gap:10,marginBottom:12,paddingBottom:10,borderBottom:`1px solid ${C.border}`}}><BookOpen size={16} color={items[0].certColor}/><span style={{fontWeight:700,color:C.t0,fontSize:14,fontFamily:mono}}>{cert}</span><span style={{fontSize:11,color:C.t2}}>({items.length})</span></div>
                  <div style={{display:'grid',gridTemplateColumns:'repeat(auto-fill,minmax(310px,1fr))',gap:10}}>{items.map(r=><AcademyCard key={r.id} r={r} t={t}/>)}</div>
                </div>
              ));
            })()}
          </>
        )}
      </div>

      <footer style={{borderTop:`1px solid ${C.border}`,padding:'20px',marginTop:40,textAlign:'center'}}>
        <p style={{fontSize:11,color:C.t2,fontFamily:mono}}>TechKB · {new Date().getFullYear()} · 12 vendors · {ARTICLES.length} articles · {totalErrorCodes} error codes · {errorStats.total_unique_codes} unique · GIN-indexed lookup</p>
      </footer>
    </div>
  );
}
