BEGIN;
INSERT INTO orders VALUES(19998,'VINET', 5, '1996-07-04', '1996-08-01', '1996-07-16', 3, 32.3800011, 'Vins et alcools Chevalier', '59 rue de l''Abbaye', 'Reims', NULL, '51100', 'France');
COMMIT;

BEGIN;
DELETE FROM orders WHERE order_id = 19998;
COMMIT;

BEGIN;
INSERT INTO orders VALUES(19999,'VINET', 5, '1996-07-04', '1996-08-01', '1996-07-16', 3, 32.3800011, 'Vins et alcools Chevalier', '59 rue de l''Abbaye', 'Reims', NULL, '51100', 'France');
DELETE FROM orders WHERE order_id = 19999;
COMMIT;

BEGIN;
INSERT INTO orders VALUES(20000,'VINET', 5, '1996-07-04', '1996-08-01', '1996-07-16', 3, 32.3800011, 'Vins et alcools Chevalier', '59 rue de l''Abbaye', 'Reims', NULL, '51100', 'France');
INSERT INTO order_details VALUES(20000,1,11,12,0);
UPDATE order_details SET quantity = 1 WHERE order_id = 20000;
UPDATE order_details SET product_id = 77 WHERE order_id = 20000;
COMMIT;

BEGIN;
UPDATE order_details SET quantity = 2 WHERE order_id = 20000;
UPDATE order_details SET quantity = 3 WHERE order_id = 20000;
UPDATE order_details SET quantity = 4 WHERE order_id = 20000;
UPDATE order_details SET quantity = 5 WHERE order_id = 20000;
COMMIT;

BEGIN;
DELETE FROM order_details WHERE order_id = 20000;
DELETE FROM orders WHERE order_id = 20000;
COMMIT;

BEGIN;
INSERT INTO orders VALUES(19991,'VINET', 5, '1996-07-04', '1996-08-01', '1996-07-16', 3, 32.3800011, 'Vins et alcools Chevalier', '59 rue de l''Abbaye', 'Reims', NULL, '51100', 'France');
ROLLBACK;
