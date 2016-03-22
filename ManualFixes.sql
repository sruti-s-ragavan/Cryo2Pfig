--C07
UPDATE logger_log SET referrer = referrer -1 where action = 'Text selection offset' and referrer > 0;
--End of C07

--D09
INSERT INTO logger_log values(0, 'c486980a-74df-40a1-b4eb-07ff1c1dff93', '2015-05-21 21:12:00.399000', 'Part activated', 
 'checking.js', '/hexcom/Current/js_v9/checking.js', '8ea5d9be-d1b5-4319-9def-495bdccb7f51', '0:47:14.179000');
INSERT INTO logger_log values(0, 'c486980a-74df-40a1-b4eb-07ff1c1dff93', '2015-05-21 21:12:00.400000', 'Text selection offset', 
'/hexcom/Current/js_v9/checking.js', '0', '8ea5d9be-d1b5-4319-9def-495bdccb7f51', '0:47:14.180000');
--End of D09

--D13
INSERT INTO logger_log values(0, 'c486980a-74df-40a1-b4eb-07ff1c1dff93', '2015-07-28 00:50:52.101000', 'Part activated', 
 'update.js', '/hexcom/Current/js_v9/update.js', '8ea5d9be-d1b5-4319-9def-495bdccb7f51', '0:22:53.194000');
INSERT INTO logger_log values(0, 'c486980a-74df-40a1-b4eb-07ff1c1dff93', '2015-07-28 00:50:52.121000', 'Text selection offset', 
'/hexcom/Current/js_v9/update.js', '0', '8ea5d9be-d1b5-4319-9def-495bdccb7f51', '0:22:53.214000');

INSERT INTO logger_log values(0, 'c486980a-74df-40a1-b4eb-07ff1c1dff93', '2015-07-28 00:52:33.466000', 'Part activated', 
 'checking.js', '/hexcom/Current/js_v9/checking.js', '8ea5d9be-d1b5-4319-9def-495bdccb7f51', '0:24:34.559000');
INSERT INTO logger_log values(0, 'c486980a-74df-40a1-b4eb-07ff1c1dff93', '2015-07-28 00:52:33.666000', 'Text selection offset', 
'/hexcom/Current/js_v9/checking.js', '0', '8ea5d9be-d1b5-4319-9def-495bdccb7f51', '0:24:34.759000');

commit
-- end of D13
