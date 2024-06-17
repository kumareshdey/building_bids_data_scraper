import * as React from 'react';
import { alpha } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TablePagination from '@mui/material/TablePagination';
import TableRow from '@mui/material/TableRow';
import TableSortLabel from '@mui/material/TableSortLabel';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Paper from '@mui/material/Paper';
import { visuallyHidden } from '@mui/utils';

interface Data {
  auction_id: number;
  address: string;
  current_bid: string;
  debt: string;
  county: string;
  city: string;
  state: string;
  remark: string;
  bid_open_date: string;
  zestimate: string;
  v_o: string;
}

const fetchData = async (
  page: number,
  pageSize: number,
  sortField: string,
  sortOrder: string,
  search: string | null
) => {
  let url = `https://aucqljn2n8.execute-api.us-east-1.amazonaws.com/auctions?page=${page}&pageSize=${pageSize}&sortField=${sortField}&sortOrder=${sortOrder}`;
  if (search) {
    url += `&search=${encodeURIComponent(search)}`;
  }
  const response = await fetch(url, {
    headers: { accept: 'application/json' },
  });
  return response.json();
};

function descendingComparator<T>(a: T, b: T, orderBy: keyof T) {
  if (b[orderBy] < a[orderBy]) {
    return -1;
  }
  if (b[orderBy] > a[orderBy]) {
    return 1;
  }
  return 0;
}

type Order = 'asc' | 'desc';

function getComparator<Key extends keyof any>(
  order: Order,
  orderBy: Key
): (a: { [key in Key]: number | string }, b: { [key in Key]: number | string }) => number {
  return order === 'desc'
    ? (a, b) => descendingComparator(a, b, orderBy)
    : (a, b) => -descendingComparator(a, b, orderBy);
}

interface HeadCell {
  disablePadding: boolean;
  id: keyof Data;
  label: string;
  numeric: boolean;
}

const headCells: readonly HeadCell[] = [
  { id: 'bid_open_date', numeric: false, disablePadding: true, label: 'Bid Open Date' },
  { id: 'city', numeric: false, disablePadding: true, label: 'City' },
  { id: 'state', numeric: false, disablePadding: true, label: 'State' },
  { id: 'county', numeric: false, disablePadding: true, label: 'County' },
  { id: 'address', numeric: false, disablePadding: true, label: 'Property Address' },
  { id: 'zestimate', numeric: false, disablePadding: true, label: 'Zestimate' },
  { id: 'debt', numeric: false, disablePadding: true, label: 'Debt' },
  { id: 'current_bid', numeric: false, disablePadding: true, label: 'Current Bid' },
  { id: 'v_o', numeric: false, disablePadding: true, label: 'V/O (Value/Owed)' },
  { id: 'remark', numeric: false, disablePadding: true, label: 'Remark' },
];

interface EnhancedTableProps {
  order: Order;
  orderBy: string;
  onRequestSort: (event: React.MouseEvent<unknown>, property: keyof Data) => void;
}

function EnhancedTableHead(props: EnhancedTableProps) {
  const { order, orderBy, onRequestSort } = props;
  const createSortHandler = (property: keyof Data) => (event: React.MouseEvent<unknown>) => {
    onRequestSort(event, property);
  };

  return (
    <TableHead>
      <TableRow>
        {headCells.map((headCell) => (
          <TableCell
            key={headCell.id}
            align={headCell.numeric ? 'right' : 'left'}
            padding={headCell.disablePadding ? 'none' : 'normal'}
            sortDirection={orderBy === headCell.id ? order : false}
            sx={{ backgroundColor: '#f5f5f5', fontWeight: 'bold' }}
          >
            <TableSortLabel
              active={orderBy === headCell.id}
              direction={orderBy === headCell.id ? order : 'asc'}
              onClick={createSortHandler(headCell.id)}
            >
              {headCell.label}
              {orderBy === headCell.id ? (
                <Box component="span" sx={visuallyHidden}>
                  {order === 'desc' ? 'sorted descending' : 'sorted ascending'}
                </Box>
              ) : null}
            </TableSortLabel>
          </TableCell>
        ))}
      </TableRow>
    </TableHead>
  );
}

export default function EnhancedTable() {
  const [order, setOrder] = React.useState<Order>('asc');
  const [orderBy, setOrderBy] = React.useState<keyof Data>('auction_id');
  const [page, setPage] = React.useState(0);
  const [rowsPerPage, setRowsPerPage] = React.useState(5);
  const [rows, setRows] = React.useState<Data[]>([]);
  const [count, setCount] = React.useState(15);
  const [search, setSearch] = React.useState<string | null>(null);

  const fetchCount = async () => {
    try {
      const response = await fetch(`https://aucqljn2n8.execute-api.us-east-1.amazonaws.com/auctions/count?search=${encodeURIComponent(search ?? '')}`);
      const data = await response.json();
      setCount(data.total_count);
    } catch (error) {
      console.error('Error fetching count:', error);
    }
  };

  React.useEffect(() => {
    fetchCount();
  }, [search]);

  const fetchRows = async () => {
    try {
      const data = await fetchData(page + 1, rowsPerPage, orderBy, order, search);
      setRows(data);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  React.useEffect(() => {
    fetchRows();
  }, [page, rowsPerPage, order, orderBy, search]);

  const handleRequestSort = (
    event: React.MouseEvent<unknown>,
    property: keyof Data
  ) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const handleChangePage = (event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleSearch = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearch(event.target.value);
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Paper sx={{ width: '100%', mb: 2 }}>
        <Toolbar
          sx={{
            pl: { sm: 2 },
            pr: { xs: 1, sm: 1 },
          }}
        >
          <Typography
            sx={{ flex: '1 1 100%' }}
            variant="h6"
            id="tableTitle"
            component="div"
          >
            Property auction data
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', ml: 1 }}>
            <Typography variant="h6" color="inherit" noWrap>
              Search:
            </Typography>
            <input type="text" onChange={handleSearch} style={{ marginLeft: 8 }} />
          </Box>
        </Toolbar>
        <TableContainer>
          <Table
            sx={{ minWidth: 750, "& .MuiButtonBase-root": { marginLeft: "17px" } }}
            aria-labelledby="tableTitle"
            size={'medium'}
          >
            <EnhancedTableHead
              order={order}
              orderBy={orderBy}
              onRequestSort={handleRequestSort}
            />
            <TableBody>
              {rows.map((row, index) => (
                <TableRow
                  hover
                  tabIndex={-1}
                  key={row.auction_id}
                >
                  <TableCell>{row.bid_open_date}</TableCell>
                  <TableCell>{row.city}</TableCell>
                  <TableCell>{row.state}</TableCell>
                  <TableCell>{row.county}</TableCell>
                  <TableCell>{row.address}</TableCell>
                  <TableCell>{row.zestimate}</TableCell>
                  <TableCell>{row.debt}</TableCell>
                  <TableCell>{row.current_bid}</TableCell>
                  <TableCell>{row.v_o}</TableCell>
                  <TableCell>{row.remark}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={count}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      </Paper>
    </Box>
  );
}
