select ename,dname
 from emp inner join dept
 on emp.deptno =dept.deptno;
 
 select  e1.ename, e2.ename AS manager
 from emp e1 join emp e2
 on e1.mgr =e2.empno;
 
 
 -- waqtd ename mgr manager's manager of all emp ?
 SELECT e.ename AS employee_name,
       m.ename AS manager_name,
       mm.ename AS manager_manager_name
FROM emp e
LEFT JOIN emp m
ON e.mgr = m.empno
LEFT JOIN emp mm
ON m.mgr = mm.empno;
-- OR
select e1.ename,e2.ename,e3.ename  managers_manager from emp  
e1 join emp e2
on e1.mgr = e2.empno
join emp e3
on e2.mgr = e3.empno;


-- waqtd ename ,dame,manager name mgr dname ,
-- managers manager name mgrs mgr dname ?
SELECT e.ename AS employee_name,
       d.dname AS employee_dept,
       m.ename AS manager_name,
       dm.dname AS manager_dept,
       mm.ename AS managers_manager_name,
       dmm.dname AS managers_manager_dept
FROM emp e
LEFT JOIN dept d
       ON e.deptno = d.deptno
LEFT JOIN emp m
       ON e.mgr = m.empno
LEFT JOIN dept dm
       ON m.deptno = dm.deptno
LEFT JOIN emp mm
       ON m.mgr = mm.empno
LEFT JOIN dept dmm
       ON mm.deptno = dmm.deptno;
       
-- OR
SELECT e1.ename, d1.dname, e2.ename, d2.dname, e3.ename, d3.dname FROM emp e1 JOIN emp e2
ON e1.mgr = e2.empno JOIN emp e3
ON e2.mgr = e3.empno JOIN dept d1
ON e1.deptno = d1.deptno JOIN dept d2
ON e2.deptno = d2.deptno JOIN dept d3
ON e3.deptno = d3.deptno;
