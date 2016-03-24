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

--D12
update logger_log set referrer = '1229' where timestamp = '2015-06-11 21:04:49.723050000';
-- End of d12

--d08

insert into logger_log values (0, 'c486980a-74df-40a1-b4eb-07ff1c1dff93', '2015-05-20 20:42:36.841', 'Part activated', 'checking.js', '/hexcom/2014-05-19-07:36:13/js/checking.js' ,  '8ea5d9be-d1b5-4319-9def-495bdccb7f51', '00:19:19.968');

insert into logger_log values (0, 'c486980a-74df-40a1-b4eb-07ff1c1dff93', '2015-05-20 20:42:36.851', 'Text selection offset', '/hexcom/2014-05-19-07:36:13/js/checking.js' , '0', '8ea5d9be-d1b5-4319-9def-495bdccb7f51', '00:19:19.978');

insert into logger_log values (0, 'c486980a-74df-40a1-b4eb-07ff1c1dff93', '2015-05-20 20:45:47.000000', 'Part activated', 'render.js', '/hexcom/Current/js_v9/render.js', '8ea5d9be-d1b5-4319-9def-495bdccb7f51', '00:22:30.127000');

 insert into logger_log values (0, 'c486980a-74df-40a1-b4eb-07ff1c1dff93', '2015-05-20 20:45:47.000300', 'Text selection offset', '/hexcom/Current/js_v9/render.js', '0', '8ea5d9be-d1b5-4319-9def-495bdccb7f51', '00:22:30.127299');
 
 insert into logger_log values (0, 'c486980a-74df-40a1-b4eb-07ff1c1dff93', '2015-05-20 20:45:47.000700', 'Part activated', 'view.js', '/hexcom/Current/js_v9/view.js', '8ea5d9be-d1b5-4319-9def-495bdccb7f51', '00:22:30.127399');
 
 insert into logger_log values (0, 'c486980a-74df-40a1-b4eb-07ff1c1dff93', '2015-05-20 20:45:47.000900', 'Text selection offset', '/hexcom/Current/js_v9/view.js', '0', '8ea5d9be-d1b5-4319-9def-495bdccb7f51', '00:22:30.1272');
 
INSERT INTO logger_log values(0, 'c486980a-74df-40a1-b4eb-07ff1c1dff93', '2015-05-20 20:49:53.722000', 'Part activated', 'checking.js', '/hexcom/2014-05-19-07:36:13/js/checking.js', '8ea5d9be-d1b5-4319-9def-495bdccb7f51', '00:26:36.849000');
 
INSERT INTO logger_log values(0, 'c486980a-74df-40a1-b4eb-07ff1c1dff93', '2015-05-20 20:49:53.725000', 'Text selection offset', '/hexcom/2014-05-19-07:36:13/js/checking.js', '550', '8ea5d9be-d1b5-4319-9def-495bdccb7f51', '00:26:36.851999');

INSERT INTO logger_log values(0, 'c486980a-74df-40a1-b4eb-07ff1c1dff93', '2015-05-20 20:49:53.727000', 'Text selection offset', '/hexcom/2014-05-19-07:36:13/js/checking.js', '150', '8ea5d9be-d1b5-4319-9def-495bdccb7f51', '00:26:36.852900');

INSERT INTO logger_log values(0, 'c486980a-74df-40a1-b4eb-07ff1c1dff93', '2015-05-20 20:51:12.041000', 'Part activated', 'main.js', '/hexcom/2014-05-19-07:36:13/main.js', '8ea5d9be-d1b5-4319-9def-495bdccb7f51', '0:27:55.168000');

INSERT INTO logger_log values(0, 'c486980a-74df-40a1-b4eb-07ff1c1dff93', '2015-05-20 20:51:12.042000', 'Text selection offset',  '/hexcom/2014-05-19-07:36:13/main.js', '0', '8ea5d9be-d1b5-4319-9def-495bdccb7f51', '0:27:55.169000');

INSERT INTO logger_log values(0, 'c486980a-74df-40a1-b4eb-07ff1c1dff93', '2015-05-20 21:10:43.548000', 'Part activated', 'update.js', '/hexcom/Current/js_v9/update.js', '8ea5d9be-d1b5-4319-9def-495bdccb7f51', '00:47:26.675');

INSERT INTO logger_log values(0, 'c486980a-74df-40a1-b4eb-07ff1c1dff93', '2015-05-20 21:10:43.648000', 'Text selection offset', '/hexcom/Current/js_v9/update.js', '0', '8ea5d9be-d1b5-4319-9def-495bdccb7f51', '00:47:26.775');

--End of d08