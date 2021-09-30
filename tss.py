import click

import submitter as sb

# @click.command()
# @click.argument('stock')
def main(stock:str) -> None:
    """Tiny stock submitter - simple tool to submit uploaded content to microstocks 
    using selenium webdriver
    
    \b
    Supported microstocks:
    123 - 123rf.com
    cs  - canstockphoto.com
    dt  - dreamstime.com
    dp  - depositphotos.com
    """

    submitter = sb.create_submitter(stock)
    submitter.run()

if __name__ == "__main__":
    # main()    
    main('dp') 