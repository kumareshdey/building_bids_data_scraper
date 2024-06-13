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
  tax_liability: string;
  date: string;
  zestimate: string;
  v_o: string;
}

const fetchData = async (
  page: number,
  pageSize: number,
  sortField: string,
  sortOrder: string
) => {
  const response = await fetch(
    `http://54.167.54.88/auctions?page=${page}&pageSize=${pageSize}&sortField=${sortField}&sortOrder=${sortOrder}`,
    {
      headers: { accept: 'application/json' },
    }
  );
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
  { id: 'city', numeric: false, disablePadding: true, label: 'City' },
  { id: 'state', numeric: false, disablePadding: true, label: 'State' },
  { id: 'county', numeric: false, disablePadding: true, label: 'County' },
  { id: 'address', numeric: false, disablePadding: true, label: 'Property Address' },
  { id: 'zestimate', numeric: false, disablePadding: true, label: 'Zestimate' },
  { id: 'debt', numeric: false, disablePadding: true, label: 'Debt' },
  { id: 'tax_liability', numeric: false, disablePadding: true, label: 'Tax Liability' },
  { id: 'current_bid', numeric: false, disablePadding: true, label: 'Current Bid' },
  { id: 'v_o', numeric: false, disablePadding: true, label: 'V/O (Value/Owed)' },
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
  const fetchCount = async () => {
    try {
      const response = await fetch('http://54.167.54.88/auctions/count'); // Replace with your endpoint
      const data = await response.json();
      setCount(data.total_count);
    } catch (error) {
      console.error('Error fetching count:', error);
    }
  };
  React.useEffect(() => {
    fetchCount();
  }, []);

  const fetchRows = async () => {
    try {
      const data = await fetchData(page + 1, rowsPerPage, orderBy, order);
      setRows(data);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  React.useEffect(() => {
    fetchRows();
  }, [page, rowsPerPage, order, orderBy]);

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
        </Toolbar>
        <TableContainer>
          <Table
            sx={{ minWidth: 750, "& .MuiButtonBase-root": {
              marginLeft: "17px"
            } }}
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
                  <TableCell>{row.city}</TableCell>
                  <TableCell>{row.state}</TableCell>
                  <TableCell>{row.county}</TableCell>
                  <TableCell>{row.address}</TableCell>
                  <TableCell>{row.zestimate}</TableCell>
                  <TableCell>{row.debt}</TableCell>
                  <TableCell>{row.tax_liability}</TableCell>
                  <TableCell>{row.current_bid}</TableCell>
                  <TableCell>{row.v_o}</TableCell>
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