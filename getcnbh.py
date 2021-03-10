import argparse
import main
import contextlib
import traceback
import logging

# 关闭日志
logging.getLogger('urllib3').setLevel(logging.ERROR)

if __name__ == "__main__":



    parser = argparse.ArgumentParser(description='得到学员的Cnbh')
    parser.add_argument('-u', action='store', dest="username",type=str,
                        help='用户名', required=True)
    parser.add_argument('-p', action='store', dest="password",type=str,
                        help='密码', required=True)

    args = parser.parse_args()

    main.password = args.password
    main.username = args.username

    with contextlib.closing(main.init_s()) as s:

        (s,xxzh) = main.try_login(s)

        try:
            cnbh = main.get_cnbh(s, xxzh=xxzh)
        except KeyError:
            traceback.print_exc()

    print(cnbh)
