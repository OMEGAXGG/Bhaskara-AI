Here's a simple Rust code example that prints "Hello, World!" to the console:

```rust
fn main() {
    println!("Hello, World!");
}
```

To run the code, save it in a file named `main.rs` and use the Rust compiler `rustc` to compile and run it:

```sh
$ rustc main.rs
$ ./main
Hello, World!
```

If you prefer a more complex example, here's a Rust code snippet that defines a simple calculator with addition, subtraction, multiplication, and division operations:

```rust
fn main() {
    let mut num1 = 10;
    let mut num2 = 5;

    println!("Addition: {}", num1 + num2);
    println!("Subtraction: {}", num1 - num2);
    println!("Multiplication: {}", num1 * num2);
    println!("Division: {}", num1 / num2);
}
```

This code defines a `main` function that initializes two integer variables `num1` and `num2` with values `10` and `5` respectively. It then prints the results of adding, subtracting, multiplying, and dividing these numbers using the `println!` macro.