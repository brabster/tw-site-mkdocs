-- order_id 19998: insert and delete, separate transactions

BEGIN;
INSERT INTO orders VALUES(19998,'VINET', 5, '1996-07-04', '1996-08-01', '1996-07-16', 3, 32.3800011, 'Vins et alcools Chevalier', '59 rue de l''Abbaye', 'Reims', NULL, '51100', 'France');
COMMIT;

BEGIN;
DELETE FROM orders WHERE order_id = 19998;
COMMIT;

-- order_id 19999: insert and delete, same transaction

BEGIN;
INSERT INTO orders VALUES(19999,'VINET', 5, '1996-07-04', '1996-08-01', '1996-07-16', 3, 32.3800011, 'Vins et alcools Chevalier', '59 rue de l''Abbaye', 'Reims', NULL, '51100', 'France');
DELETE FROM orders WHERE order_id = 19999;
COMMIT;

-- order_id 20000: insert and update, separate transactions

BEGIN;
INSERT INTO orders VALUES(20000,'VINET', 5, '1996-07-04', '1996-08-01', '1996-07-16', 3, 32.3800011, 'Vins et alcools Chevalier', '59 rue de l''Abbaye', 'Reims', NULL, '51100', 'France');
INSERT INTO order_details VALUES(20000,1,11,12,0);
UPDATE order_details SET quantity = 1 WHERE order_id = 20000;
UPDATE order_details SET product_id = 77 WHERE order_id = 20000;
COMMIT;

BEGIN;
UPDATE order_details SET quantity = 2 WHERE order_id = 20000;
UPDATE order_details SET quantity = 3 WHERE order_id = 20000;
UPDATE orders SET ship_address = '58 rue de l''Abbaye' WHERE order_id = 20000;
UPDATE order_details SET quantity = 4 WHERE order_id = 20000;
UPDATE order_details SET quantity = 5 WHERE order_id = 20000;
COMMIT;

BEGIN;
DELETE FROM order_details WHERE order_id = 20000;
DELETE FROM orders WHERE order_id = 20000;
COMMIT;

-- order_id 20001, insert and rollback

BEGIN;
INSERT INTO orders VALUES(20001,'VINET', 5, '1996-07-04', '1996-08-01', '1996-07-16', 3, 32.3800011, 'Vins et alcools Chevalier', '59 rue de l''Abbaye', 'Reims', NULL, '51100', 'France');
ROLLBACK;

-- simulates queuing of statements in a transaction as user makes edits
BEGIN;
-- create record
INSERT INTO orders VALUES(20002,'VINET', 5, '1996-07-04', '1996-07-05', '1996-08-02', 3, 32.3800011, 'Vins et alcools Chevalier', '59 rue de l''Abbaye', 'Reims', NULL, '51100', 'France');
-- user selects required_date field and changes it
UPDATE orders SET required_date = '1996-09-01' WHERE order_id = 20002;
-- user selects required_date field and changes it again
UPDATE orders SET required_date = '1996-08-25' WHERE order_id = 20002;
-- user selects ship_address field and changes it
UPDATE orders SET ship_address = '60 rue de l''Abbaye' WHERE order_id = 20002;
-- user sets the shipped_date
UPDATE orders SET shipped_date = '1996-08-01' WHERE order_id = 20002;
-- user hits save
COMMIT;

BEGIN;
-- user goes back into the record and makes another update
UPDATE orders SET required_date = '1996-07-10' WHERE order_id = 20002;
-- then saves
COMMIT;