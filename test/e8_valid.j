class Main {
	 Void main(){

	 	Int i;
		Int j;
		i = j;
	 }

 }

 class Delivery {

	Driver driver;
 	Int i;
	Int j;
	Int p;
	String k;
	Bool q;

	Void deliver() {

		driver = new Driver();
		k = driver.getName();
		i = driver.deliverOrder();
		i = driver.deliverOrder(i);
		i = driver.deliverOrder(i, j);
		p = driver.deliverOrder(i, j, q);

	}

 }

 class Driver {

	Int a;
	Bool b;
	String name;


	Int deliverOrder() {
		return 0;
	}
	Int deliverOrder(Int a) {
		return a;
	}
	String deliverOrder(Int t) {
		return 37;
	}
	Int deliverOrder(Int a, Int b) {
		return a+b;
	}
	Int deliverOrder(Int a, Int b, Bool c) {
		if (c) {
			return a + b;
		} else {
			return a - b;
		}
	}
	String getName() {
		return this.name;
	}
	Void testOnly() {
		return;
	}


 }
