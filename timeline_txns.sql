-- 29999 single-table

BEGIN;
INSERT INTO orders VALUES(29999,'VINET', 5, CURRENT_DATE - INTERVAL '40' day, CURRENT_DATE - INTERVAL '3' day, CURRENT_DATE - INTERVAL '12' day, 3, 32.3800011, 'Vins et alcools Chevalier', '59 rue de l''Abbaye', 'Reims', NULL, '51100', 'France');
COMMIT;

BEGIN;
UPDATE orders SET ship_address = '59 rue de l''Abbaye' WHERE order_id = '29999';
COMMIT;

BEGIN;
UPDATE orders SET required_date = CURRENT_DATE - INTERVAL '2' day WHERE order_id = '29999';
COMMIT;

BEGIN;
UPDATE orders SET ship_address = '60 rue de l''Abbaye' WHERE order_id = '29999';
COMMIT;

BEGIN;
UPDATE orders SET required_date = CURRENT_DATE - INTERVAL '1' day WHERE order_id = '29999';
COMMIT;


-- 30000 single-transaction

BEGIN;
INSERT INTO orders VALUES(30000,'VINET', 5, CURRENT_DATE - INTERVAL '40' day, CURRENT_DATE - INTERVAL '3' day, CURRENT_DATE - INTERVAL '12' day, 3, 32.3800011, 'Vins et alcools Chevalier', '59 rue de l''Abbaye', 'Reims', NULL, '51100', 'France');
INSERT INTO order_details VALUES(30000,1,11,12,0);
UPDATE order_details SET quantity = 1 WHERE order_id = 30000;
UPDATE order_details SET product_id = 77 WHERE order_id = 30000;
COMMIT;

-- 30001 multi-transaction

BEGIN;
INSERT INTO orders VALUES(30001,'VINET', 5, CURRENT_DATE - INTERVAL '10' day, CURRENT_DATE + INTERVAL '10', NULL, 3, 32.3800011, 'Vins et alcools Chevalier', '59 rue de l''Abbaye', 'Reims', NULL, '51100', 'France');
COMMIT;

BEGIN;
INSERT INTO order_details VALUES(30001,1,11,12,0);
UPDATE order_details SET quantity = 1 WHERE order_id = 30001;
UPDATE order_details SET product_id = 77 WHERE order_id = 30001;
COMMIT;

BEGIN;
UPDATE orders SET required_date = CURRENT_DATE + INTERVAL '5' day WHERE order_id = 30001;
COMMIT;

BEGIN;
UPDATE orders SET shipped_date = CURRENT_DATE WHERE order_id = 30001;
COMMIT;

-- 30002 multi-transaction ends deleted

BEGIN;
INSERT INTO orders VALUES(30002,'VINET', 5, CURRENT_DATE - INTERVAL '40' day, CURRENT_DATE - INTERVAL '3' day, NULL, 3, 32.3800011, 'Vins et alcools Chevalier', '59 rue de l''Abbaye', 'Reims', NULL, '51100', 'France');
COMMIT;

BEGIN;
INSERT INTO order_details VALUES(30002,1,11,12,0);
UPDATE order_details SET quantity = 1 WHERE order_id = 30002;
UPDATE order_details SET product_id = 77 WHERE order_id = 30002;
COMMIT;

BEGIN;
UPDATE order_details SET product_id = 66 WHERE order_id = 30002;
COMMIT;

BEGIN;
DELETE FROM order_details WHERE order_id = 30002;
DELETE FROM orders WHERE order_id = 30002;
COMMIT;

-- 30003 transaction rollback

BEGIN;
INSERT INTO orders VALUES(30003,'VINET', 5, CURRENT_DATE - INTERVAL '40' day, CURRENT_DATE - INTERVAL '3' day, NULL, 3, 32.3800011, 'Vins et alcools Chevalier', '59 rue de l''Abbaye', 'Reims', NULL, '51100', 'France');
ROLLBACK;

-- 30004 multi-transaction ambiguous changes to order_details

BEGIN;
INSERT INTO orders VALUES(30004,'VINET', 5, CURRENT_DATE - INTERVAL '40' day, CURRENT_DATE - INTERVAL '3' day, NULL, 3, 32.3800011, 'Vins et alcools Chevalier', '59 rue de l''Abbaye', 'Reims', NULL, '51100', 'France');
COMMIT;

BEGIN;
INSERT INTO order_details VALUES(30004,1,11,12,0);
COMMIT;

BEGIN;
INSERT INTO order_details VALUES(30004,2,11,12,0);
UPDATE order_details SET product_id = 66 WHERE order_id = 30004 AND product_id = 1;
INSERT INTO order_details VALUES(30004,3,11,12,0);
COMMIT;

BEGIN;
UPDATE order_details SET product_id = 77 WHERE order_id = 30004 AND product_id = 2;
COMMIT;

-- 30005 unambiguous changes in order_details

BEGIN;
INSERT INTO orders VALUES(30005,'VINET', 5, CURRENT_DATE - INTERVAL '40' day, CURRENT_DATE - INTERVAL '3' day, NULL, 3, 32.3800011, 'Vins et alcools Chevalier', '59 rue de l''Abbaye', 'Reims', NULL, '51100', 'France');
COMMIT;

BEGIN;
INSERT INTO order_details VALUES(30005,1,11,12,0);
INSERT INTO order_details VALUES(30005,2,11,12,0);
COMMIT;

BEGIN;
UPDATE order_details SET quantity = 1 WHERE order_id = 30005 AND product_id = 1;
COMMIT;

BEGIN;
UPDATE order_details SET quantity = 2 WHERE order_id = 30005 AND product_id = 1;
COMMIT;

BEGIN;
DELETE FROM order_details WHERE order_id = 30005 AND product_id = 1;
COMMIT;

-- cleanup

BEGIN;
DELETE FROM order_details WHERE order_id >= 30000;
DELETE FROM orders WHERE order_id >= 30000;
COMMIT;