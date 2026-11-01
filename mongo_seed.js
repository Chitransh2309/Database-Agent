// Run with mongosh.
// Database: copilot_db
// WARNING: drops/recreates the three project collections.

use copilot_db;

db.customer_activity.drop();
db.product_reviews.drop();
db.support_tickets.drop();

db.customer_activity.insertMany([
{customer_id:1,sessions:42,page_views:310,last_active:ISODate("2026-08-20"),location:{city:"Delhi",country:"India"},devices:[{type:"mobile",sessions:25},{type:"desktop",sessions:17}],monthly:{jan:18,feb:22,mar:30,apr:28,may:35,jun:31,jul:38,aug:42}},
{customer_id:2,sessions:18,page_views:140,last_active:ISODate("2026-08-18"),location:{city:"Hyderabad",country:"India"},devices:[{type:"mobile",sessions:12},{type:"desktop",sessions:6}],monthly:{jan:8,feb:12,mar:14,apr:11,may:15,jun:17,jul:16,aug:18}},
{customer_id:3,sessions:55,page_views:520,last_active:ISODate("2026-08-22"),location:{city:"Mumbai",country:"India"},devices:[{type:"mobile",sessions:30},{type:"desktop",sessions:25}],monthly:{jan:25,feb:31,mar:38,apr:42,may:47,jun:49,jul:52,aug:55}},
{customer_id:4,sessions:12,page_views:90,last_active:ISODate("2026-08-10"),location:{city:"Bengaluru",country:"India"},devices:[{type:"mobile",sessions:8},{type:"desktop",sessions:4}],monthly:{jan:7,feb:9,mar:10,apr:8,may:11,jun:12,jul:10,aug:12}},
{customer_id:5,sessions:47,page_views:430,last_active:ISODate("2026-08-21"),location:{city:"Delhi",country:"India"},devices:[{type:"mobile",sessions:29},{type:"desktop",sessions:18}],monthly:{jan:20,feb:25,mar:31,apr:35,may:39,jun:41,jul:44,aug:47}},
{customer_id:6,sessions:22,page_views:180,last_active:ISODate("2026-08-15"),location:{city:"Chennai",country:"India"},devices:[{type:"mobile",sessions:15},{type:"desktop",sessions:7}],monthly:{jan:11,feb:14,mar:16,apr:18,may:20,jun:19,jul:21,aug:22}},
{customer_id:7,sessions:31,page_views:260,last_active:ISODate("2026-08-19"),location:{city:"Ahmedabad",country:"India"},devices:[{type:"mobile",sessions:18},{type:"desktop",sessions:13}],monthly:{jan:13,feb:17,mar:20,apr:22,may:25,jun:27,jul:29,aug:31}},
{customer_id:8,sessions:15,page_views:110,last_active:ISODate("2026-08-11"),location:{city:"Pune",country:"India"},devices:[{type:"mobile",sessions:9},{type:"desktop",sessions:6}],monthly:{jan:8,feb:10,mar:11,apr:12,may:13,jun:14,jul:14,aug:15}},
{customer_id:9,sessions:63,page_views:610,last_active:ISODate("2026-08-23"),location:{city:"Hyderabad",country:"India"},devices:[{type:"mobile",sessions:35},{type:"desktop",sessions:28}],monthly:{jan:28,feb:35,mar:40,apr:45,may:50,jun:54,jul:59,aug:63}},
{customer_id:10,sessions:9,page_views:70,last_active:ISODate("2026-08-05"),location:{city:"Kochi",country:"India"},devices:[{type:"mobile",sessions:7},{type:"desktop",sessions:2}],monthly:{jan:5,feb:7,mar:8,apr:7,may:8,jun:9,jul:8,aug:9}},
{customer_id:11,sessions:36,page_views:295,last_active:ISODate("2026-08-20"),location:{city:"Pune",country:"India"},devices:[{type:"mobile",sessions:21},{type:"desktop",sessions:15}],monthly:{jan:15,feb:19,mar:23,apr:25,may:29,jun:31,jul:33,aug:36}},
{customer_id:12,sessions:24,page_views:205,last_active:ISODate("2026-08-16"),location:{city:"Jaipur",country:"India"},devices:[{type:"mobile",sessions:14},{type:"desktop",sessions:10}],monthly:{jan:10,feb:13,mar:16,apr:17,may:19,jun:20,jul:22,aug:24}},
{customer_id:13,sessions:51,page_views:470,last_active:ISODate("2026-08-22"),location:{city:"Kolkata",country:"India"},devices:[{type:"mobile",sessions:27},{type:"desktop",sessions:24}],monthly:{jan:23,feb:28,mar:34,apr:37,may:42,jun:45,jul:48,aug:51}},
{customer_id:14,sessions:11,page_views:82,last_active:ISODate("2026-08-09"),location:{city:"Kochi",country:"India"},devices:[{type:"mobile",sessions:7},{type:"desktop",sessions:4}],monthly:{jan:5,feb:7,mar:9,apr:8,may:10,jun:9,jul:10,aug:11}},
{customer_id:15,sessions:44,page_views:390,last_active:ISODate("2026-08-21"),location:{city:"Noida",country:"India"},devices:[{type:"mobile",sessions:26},{type:"desktop",sessions:18}],monthly:{jan:18,feb:23,mar:28,apr:31,may:35,jun:38,jul:41,aug:44}},
{customer_id:16,sessions:33,page_views:270,last_active:ISODate("2026-08-18"),location:{city:"Mumbai",country:"India"},devices:[{type:"mobile",sessions:20},{type:"desktop",sessions:13}],monthly:{jan:14,feb:18,mar:21,apr:24,may:27,jun:29,jul:31,aug:33}},
{customer_id:17,sessions:39,page_views:325,last_active:ISODate("2026-08-19"),location:{city:"Chandigarh",country:"India"},devices:[{type:"mobile",sessions:22},{type:"desktop",sessions:17}],monthly:{jan:16,feb:21,mar:25,apr:28,may:31,jun:34,jul:37,aug:39}},
{customer_id:18,sessions:27,page_views:210,last_active:ISODate("2026-08-15"),location:{city:"Ahmedabad",country:"India"},devices:[{type:"mobile",sessions:16},{type:"desktop",sessions:11}],monthly:{jan:12,feb:15,mar:18,apr:20,may:22,jun:24,jul:25,aug:27}},
{customer_id:19,sessions:14,page_views:105,last_active:ISODate("2026-08-12"),location:{city:"Gurugram",country:"India"},devices:[{type:"mobile",sessions:8},{type:"desktop",sessions:6}],monthly:{jan:7,feb:8,mar:9,apr:10,may:12,jun:11,jul:13,aug:14}},
{customer_id:20,sessions:58,page_views:575,last_active:ISODate("2026-08-23"),location:{city:"Chennai",country:"India"},devices:[{type:"mobile",sessions:33},{type:"desktop",sessions:25}],monthly:{jan:27,feb:32,mar:39,apr:43,may:47,jun:50,jul:54,aug:58}},
{customer_id:21,sessions:20,page_views:155,last_active:ISODate("2026-08-14"),location:{city:"Bengaluru",country:"India"},devices:[{type:"mobile",sessions:13},{type:"desktop",sessions:7}],monthly:{jan:9,feb:12,mar:13,apr:15,may:16,jun:17,jul:19,aug:20}},
{customer_id:22,sessions:46,page_views:405,last_active:ISODate("2026-08-21"),location:{city:"Hyderabad",country:"India"},devices:[{type:"mobile",sessions:28},{type:"desktop",sessions:18}],monthly:{jan:19,feb:24,mar:29,apr:32,may:36,jun:39,jul:43,aug:46}},
{customer_id:23,sessions:8,page_views:61,last_active:ISODate("2026-08-06"),location:{city:"Shimla",country:"India"},devices:[{type:"mobile",sessions:5},{type:"desktop",sessions:3}],monthly:{jan:4,feb:6,mar:5,apr:7,may:6,jun:8,jul:7,aug:8}},
{customer_id:24,sessions:29,page_views:230,last_active:ISODate("2026-08-17"),location:{city:"Lucknow",country:"India"},devices:[{type:"mobile",sessions:17},{type:"desktop",sessions:12}],monthly:{jan:12,feb:16,mar:19,apr:21,may:23,jun:25,jul:27,aug:29}},
{customer_id:25,sessions:61,page_views:590,last_active:ISODate("2026-08-24"),location:{city:"Jaipur",country:"India"},devices:[{type:"mobile",sessions:34},{type:"desktop",sessions:27}],monthly:{jan:29,feb:34,mar:40,apr:45,may:49,jun:53,jul:57,aug:61}},
{customer_id:26,sessions:17,page_views:125,last_active:ISODate("2026-08-13"),location:{city:"Kolkata",country:"India"},devices:[{type:"mobile",sessions:10},{type:"desktop",sessions:7}],monthly:{jan:8,feb:10,mar:12,apr:13,may:14,jun:15,jul:16,aug:17}},
{customer_id:27,sessions:49,page_views:445,last_active:ISODate("2026-08-22"),location:{city:"Indore",country:"India"},devices:[{type:"mobile",sessions:29},{type:"desktop",sessions:20}],monthly:{jan:21,feb:26,mar:31,apr:34,may:38,jun:42,jul:46,aug:49}},
{customer_id:28,sessions:13,page_views:97,last_active:ISODate("2026-08-10"),location:{city:"Nagpur",country:"India"},devices:[{type:"mobile",sessions:8},{type:"desktop",sessions:5}],monthly:{jan:6,feb:8,mar:9,apr:10,may:11,jun:10,jul:12,aug:13}},
{customer_id:29,sessions:52,page_views:480,last_active:ISODate("2026-08-23"),location:{city:"Visakhapatnam",country:"India"},devices:[{type:"mobile",sessions:30},{type:"desktop",sessions:22}],monthly:{jan:22,feb:28,mar:33,apr:37,may:41,jun:45,jul:49,aug:52}},
{customer_id:30,sessions:34,page_views:285,last_active:ISODate("2026-08-20"),location:{city:"Kochi",country:"India"},devices:[{type:"mobile",sessions:19},{type:"desktop",sessions:15}],monthly:{jan:14,feb:18,mar:22,apr:25,may:27,jun:29,jul:32,aug:34}}
]);

db.product_reviews.insertMany([
{review_id:"R001",product_id:1,customer_id:1,rating:5,sentiment:"positive",review:"Excellent performance and battery life.",tags:["performance","battery","premium"],verified_purchase:true,helpful_votes:42},
{review_id:"R002",product_id:1,customer_id:3,rating:4,sentiment:"positive",review:"Very powerful but slightly expensive.",tags:["performance","price"],verified_purchase:true,helpful_votes:31},
{review_id:"R003",product_id:1,customer_id:5,rating:5,sentiment:"positive",review:"Great laptop for development work.",tags:["development","performance"],verified_purchase:true,helpful_votes:55},
{review_id:"R004",product_id:2,customer_id:11,rating:4,sentiment:"positive",review:"Lightweight and good for travel.",tags:["portable","battery"],verified_purchase:true,helpful_votes:18},
{review_id:"R005",product_id:3,customer_id:2,rating:5,sentiment:"positive",review:"Great camera and display.",tags:["camera","display"],verified_purchase:true,helpful_votes:47},
{review_id:"R006",product_id:3,customer_id:9,rating:4,sentiment:"positive",review:"Fast phone with excellent performance.",tags:["performance","speed"],verified_purchase:true,helpful_votes:26},
{review_id:"R007",product_id:4,customer_id:6,rating:4,sentiment:"positive",review:"Good value for the price.",tags:["value","budget"],verified_purchase:true,helpful_votes:19},
{review_id:"R008",product_id:5,customer_id:4,rating:4,sentiment:"positive",review:"Sharp display and good colors.",tags:["display","office"],verified_purchase:true,helpful_votes:22},
{review_id:"R009",product_id:6,customer_id:8,rating:5,sentiment:"positive",review:"Perfect size for a home office.",tags:["office","display"],verified_purchase:true,helpful_votes:14},
{review_id:"R010",product_id:7,customer_id:1,rating:5,sentiment:"positive",review:"Excellent typing experience.",tags:["typing","mechanical"],verified_purchase:true,helpful_votes:36},
{review_id:"R011",product_id:7,customer_id:13,rating:4,sentiment:"positive",review:"Solid keyboard with good switches.",tags:["switches","typing"],verified_purchase:true,helpful_votes:17},
{review_id:"R012",product_id:8,customer_id:15,rating:4,sentiment:"positive",review:"Comfortable and responsive.",tags:["mouse","comfort"],verified_purchase:true,helpful_votes:13},
{review_id:"R013",product_id:9,customer_id:16,rating:3,sentiment:"neutral",review:"Works well but gets warm.",tags:["usb","heat"],verified_purchase:true,helpful_votes:8},
{review_id:"R014",product_id:10,customer_id:3,rating:5,sentiment:"positive",review:"Very comfortable for long listening sessions.",tags:["audio","comfort"],verified_purchase:true,helpful_votes:39},
{review_id:"R015",product_id:10,customer_id:20,rating:4,sentiment:"positive",review:"Strong noise cancellation.",tags:["noise-cancellation","audio"],verified_purchase:true,helpful_votes:28},
{review_id:"R016",product_id:11,customer_id:12,rating:4,sentiment:"positive",review:"Good sound for the price.",tags:["audio","value"],verified_purchase:true,helpful_votes:11},
{review_id:"R017",product_id:12,customer_id:5,rating:3,sentiment:"neutral",review:"Good features but battery could be better.",tags:["battery","features"],verified_purchase:true,helpful_votes:21},
{review_id:"R018",product_id:13,customer_id:18,rating:4,sentiment:"positive",review:"Useful for daily fitness tracking.",tags:["fitness","health"],verified_purchase:true,helpful_votes:12},
{review_id:"R019",product_id:14,customer_id:6,rating:5,sentiment:"positive",review:"Excellent tablet for studying.",tags:["study","display"],verified_purchase:true,helpful_votes:25},
{review_id:"R020",product_id:14,customer_id:24,rating:4,sentiment:"positive",review:"Good screen and performance.",tags:["display","performance"],verified_purchase:true,helpful_votes:16},
{review_id:"R021",product_id:15,customer_id:10,rating:4,sentiment:"positive",review:"Compact and convenient.",tags:["portable","tablet"],verified_purchase:true,helpful_votes:9},
{review_id:"R022",product_id:16,customer_id:17,rating:5,sentiment:"positive",review:"Very comfortable for long work sessions.",tags:["office","comfort"],verified_purchase:true,helpful_votes:32},
{review_id:"R023",product_id:17,customer_id:19,rating:4,sentiment:"positive",review:"Comfortable and affordable.",tags:["office","value"],verified_purchase:true,helpful_votes:15},
{review_id:"R024",product_id:18,customer_id:25,rating:5,sentiment:"positive",review:"Standing desk improved my workspace.",tags:["desk","ergonomics"],verified_purchase:true,helpful_votes:41},
{review_id:"R025",product_id:19,customer_id:22,rating:4,sentiment:"positive",review:"Spacious and durable backpack.",tags:["travel","storage"],verified_purchase:true,helpful_votes:10},
{review_id:"R026",product_id:20,customer_id:27,rating:3,sentiment:"neutral",review:"Decent quality for video calls.",tags:["camera","video"],verified_purchase:true,helpful_votes:7},
{review_id:"R027",product_id:21,customer_id:29,rating:5,sentiment:"positive",review:"Fast transfer speeds.",tags:["storage","speed"],verified_purchase:true,helpful_votes:29},
{review_id:"R028",product_id:22,customer_id:30,rating:4,sentiment:"positive",review:"Reliable backup drive.",tags:["storage","backup"],verified_purchase:true,helpful_votes:13},
{review_id:"R029",product_id:23,customer_id:7,rating:4,sentiment:"positive",review:"Stable connection throughout the house.",tags:["network","wifi"],verified_purchase:true,helpful_votes:18},
{review_id:"R030",product_id:24,customer_id:28,rating:3,sentiment:"neutral",review:"Large capacity but charging is slow.",tags:["power","charging"],verified_purchase:true,helpful_votes:6},
{review_id:"R031",product_id:25,customer_id:9,rating:5,sentiment:"positive",review:"Clear audio for meetings.",tags:["microphone","meetings"],verified_purchase:true,helpful_votes:24},
{review_id:"R032",product_id:1,customer_id:13,rating:4,sentiment:"positive",review:"Excellent for development and machine learning.",tags:["development","machine-learning"],verified_purchase:true,helpful_votes:33},
{review_id:"R033",product_id:3,customer_id:20,rating:5,sentiment:"positive",review:"Camera quality is outstanding.",tags:["camera","photography"],verified_purchase:true,helpful_votes:44},
{review_id:"R034",product_id:10,customer_id:25,rating:5,sentiment:"positive",review:"Best headphones I have used.",tags:["audio","noise-cancellation"],verified_purchase:true,helpful_votes:51},
{review_id:"R035",product_id:18,customer_id:29,rating:4,sentiment:"positive",review:"Strong desk and easy assembly.",tags:["desk","assembly"],verified_purchase:true,helpful_votes:20}
]);

db.support_tickets.insertMany([
{ticket_id:"T001",customer_id:1,created_at:ISODate("2026-07-04"),category:"Payment",priority:"High",status:"Resolved",issue:"Payment failed during checkout",metadata:{channel:"web",browser:"Chrome",device:"mobile"}},
{ticket_id:"T002",customer_id:3,created_at:ISODate("2026-07-11"),category:"Product",priority:"Medium",status:"Open",issue:"Laptop overheating during heavy workloads",metadata:{channel:"mobile",browser:"Chrome",device:"desktop"}},
{ticket_id:"T003",customer_id:5,created_at:ISODate("2026-07-18"),category:"Delivery",priority:"High",status:"Resolved",issue:"Order delivered late",metadata:{channel:"web",browser:"Edge",device:"mobile"}},
{ticket_id:"T004",customer_id:9,created_at:ISODate("2026-07-22"),category:"Account",priority:"Low",status:"Open",issue:"Unable to update profile information",metadata:{channel:"mobile",browser:"Safari",device:"mobile"}},
{ticket_id:"T005",customer_id:13,created_at:ISODate("2026-07-25"),category:"Product",priority:"Medium",status:"Resolved",issue:"Tablet performance slower than expected",metadata:{channel:"web",browser:"Chrome",device:"desktop"}},
{ticket_id:"T006",customer_id:20,created_at:ISODate("2026-07-29"),category:"Delivery",priority:"High",status:"Open",issue:"Delivery tracking has not updated",metadata:{channel:"web",browser:"Firefox",device:"desktop"}},
{ticket_id:"T007",customer_id:25,created_at:ISODate("2026-08-02"),category:"Payment",priority:"Medium",status:"Resolved",issue:"Duplicate payment notification",metadata:{channel:"mobile",browser:"Chrome",device:"mobile"}},
{ticket_id:"T008",customer_id:27,created_at:ISODate("2026-08-04"),category:"Product",priority:"Low",status:"Resolved",issue:"Webcam image appears blurry",metadata:{channel:"web",browser:"Edge",device:"desktop"}},
{ticket_id:"T009",customer_id:29,created_at:ISODate("2026-08-08"),category:"Technical",priority:"High",status:"Open",issue:"Storage device disconnects intermittently",metadata:{channel:"web",browser:"Chrome",device:"desktop"}},
{ticket_id:"T010",customer_id:2,created_at:ISODate("2026-08-10"),category:"Account",priority:"Low",status:"Resolved",issue:"Requested email address update",metadata:{channel:"mobile",browser:"Chrome",device:"mobile"}},
{ticket_id:"T011",customer_id:4,created_at:ISODate("2026-08-12"),category:"Delivery",priority:"Medium",status:"Resolved",issue:"Package arrived with damaged outer box",metadata:{channel:"web",browser:"Chrome",device:"desktop"}},
{ticket_id:"T012",customer_id:15,created_at:ISODate("2026-08-14"),category:"Payment",priority:"High",status:"Open",issue:"Card payment repeatedly declined",metadata:{channel:"web",browser:"Edge",device:"desktop"}},
{ticket_id:"T013",customer_id:17,created_at:ISODate("2026-08-15"),category:"Product",priority:"Medium",status:"Open",issue:"Office chair adjustment mechanism is stiff",metadata:{channel:"mobile",browser:"Chrome",device:"mobile"}},
{ticket_id:"T014",customer_id:22,created_at:ISODate("2026-08-17"),category:"Account",priority:"Low",status:"Resolved",issue:"Unable to change notification preferences",metadata:{channel:"web",browser:"Firefox",device:"desktop"}},
{ticket_id:"T015",customer_id:30,created_at:ISODate("2026-08-20"),category:"Delivery",priority:"Medium",status:"Resolved",issue:"Requested delivery date change",metadata:{channel:"mobile",browser:"Safari",device:"mobile"}}
]);

print("customer_activity:",db.customer_activity.countDocuments());
print("product_reviews:",db.product_reviews.countDocuments());
print("support_tickets:",db.support_tickets.countDocuments());
